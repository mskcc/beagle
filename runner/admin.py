import re
import json
from django.contrib import admin, messages
from django.urls import reverse
from django.conf import settings
from django.utils.translation import ngettext
from django.utils.html import format_html, format_html_join
from lib.admin import link_relation, progress_bar
from beagle.settings import RIDGEBACK_URL
from rangefilter.filter import DateTimeRangeFilter
from runner.tasks import terminate_job_task, add_pipeline_to_cache
from advanced_filters.admin import AdminAdvancedFiltersMixin
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger, RunStatus, PipelineName, OperatorSDK


def action_add_pipeline_to_cache(modeladmin, request, queryset):
    for pipeline in queryset:
        add_pipeline_to_cache.delay(pipeline.github, pipeline.version)


action_add_pipeline_to_cache.short_description = "Add Pipeline to Cache"


class PipelineAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "pipeline_name_string",
        "name",
        "version",
        "default",
        "output_directory",
        link_relation("operator"),
    )
    actions = [
        action_add_pipeline_to_cache,
    ]
    list_filter = ("default",)
    advanced_filter_fields = ("default",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("github", "version")
        else:
            return []

    def pipeline_name_string(self, obj):
        if not obj.pipeline_name:
            return "-"
        return obj.pipeline_name.name


class AppFilter(admin.SimpleListFilter):
    title = "App"
    parameter_name = "app"

    def lookups(self, request, model_admin):
        options = list()

        for o in Pipeline.objects.order_by("-default", "name").values("id", "name", "version", "default"):
            check = " ✓" if o["default"] else ""
            options.append((o["id"], "%s %s%s" % (o["name"], o["version"], check)))
        return options

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(app_id=self.value())
        return queryset


class StatusFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        # TODO support range in status count
        filters = {
            k: v
            for (k, v) in request.GET.items()
            if "range" not in k and "status" not in k and "q" not in k and "p" not in k and "o" not in k
        }

        qs = model_admin.get_queryset(request).filter(**filters)
        if request.GET.get("q"):
            qs, _use_distinct = model_admin.get_search_results(request, qs, request.GET.get("q"))
        return [
            (status.value, "%s (%s)" % (status.name, qs.filter(status=status.value).count())) for status in RunStatus
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


def terminate_run(modeladmin, request, queryset):
    jobs = list(queryset.values_list("id", flat=True))
    updated = len(jobs)
    terminate_job_task.delay(None, jobs)
    modeladmin.message_user(
        request,
        ngettext(
            "%d job was submitted to be cancelled",
            "%d jobs were submitted to be cancelled",
            updated,
        )
        % updated,
        messages.SUCCESS,
    )


terminate_run.short_description = "Terminate Run"


class RunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        link_relation("app"),
        link_relation("operator_run"),
        "tags",
        "status",
        "link_to_ridgeback",
        "created_date",
        "finished_date",
    )
    ordering = ("-created_date",)
    list_filter = (
        ("created_date", DateTimeRangeFilter),
        StatusFilter,
        AppFilter,
    )
    search_fields = (
        "tags__{sample_id_key}".format(sample_id_key=settings.SAMPLE_ID_METADATA_KEY),
        "tags__igoRequestId",
        "tags__cmoSampleIds__contains",
        "operator_run__id",
    )
    readonly_fields = (
        "samples",
        "job_group",
        "job_group_notifier",
        link_relation("operator_run"),
        link_relation("app"),
    )

    actions = [terminate_run]

    def link_to_ridgeback(self, obj):
        if not obj.execution_id:
            return "-"
        return format_html(
            "<a target='_blank' href='{ridgeback_url}/admin/orchestrator/job/{execution_id}'>{execution_id}</a>",
            execution_id=obj.execution_id,
            ridgeback_url=RIDGEBACK_URL,
        )

    link_to_ridgeback.short_description = "Execution ID (Ridgeback)"


class OperatorRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        link_relation("operator"),
        "first_run",
        "status",
        "run_count",
        progress_bar("percent_runs_succeeded"),
        progress_bar("percent_runs_finished"),
        "created_date",
    )
    ordering = ("-created_date",)
    readonly_fields = ("id", "operator", "job_group", "job_group_notifier", "parent")

    def run_count(self, obj):
        return obj.runs.count()

    def first_run(self, obj):
        run = obj.runs.first()
        if run:
            url = reverse("admin:{}_{}_change".format(obj._meta.app_label, "run"), args=(run.pk,))
            return format_html("<a href='{url}'>{name}</a>", url=url, name=run.name)


class OperatorTriggerAdmin(admin.ModelAdmin):
    list_display = ("id", link_relation("from_operator"), link_relation("to_operator"), "aggregate_condition", "graph")

    def _get_adjacent_nodes(self, operator, nodes=[], connections=[]):
        adjacent = OperatorTrigger.objects.filter(from_operator=operator)
        new_nodes = [
            {
                "key": str(node.to_operator.id),
                "pipeline": str(node.to_operator.pipeline_set.filter(default=True).first().id)
                if node.to_operator.pipeline_set.filter(default=True).first()
                else "",
                "text": node.to_operator.slug,
                "category": "Default",
            }
            for node in adjacent
        ]
        new_connections = [{"from": str(operator.id), "to": str(node.to_operator.id)} for node in adjacent]
        nodes.extend(new_nodes)
        connections.extend(new_connections)
        adjacent_nodes = [node.to_operator for node in adjacent]
        return adjacent_nodes, nodes, connections

    def graph(self, obj):
        """
        {"class": "go.GraphLinksModel",
                "copiesArrays": True,
                "copiesArrayObjects": True,
                "nodeDataArray": [
                    {"key": 0, "text": "ArgosOperator_v1.1.0"},
                    {"key": 1, "text": "ArgosQcOperator_v1.1.0"},
                    {"key": 2, "text": "CopyOutputsOperator_v1.1.0"},
                    {"key": 3, "text": "HelixFiltersOperator_v20.11.2"}
                ],
                "linkDataArray": [
                    {"from": 0, "to": 1},
                    {"from": 0, "to": 2},
                    {"from": 0, "to": 3}
                ]
            }
        """
        first_operator = obj.from_operator
        nodes = [
            {
                "key": str(first_operator.id),
                "pipeline": str(first_operator.pipeline_set.filter(default=True).first().id)
                if first_operator.pipeline_set.filter(default=True).first()
                else "",
                "text": first_operator.slug,
                "category": "Selected",
            }
        ]
        connections = []
        adjacent, nodes, connections = self._get_adjacent_nodes(first_operator, nodes, connections)
        while adjacent:
            next_adjacent = []
            for item in adjacent:
                new_adjacent, nodes, connections = self._get_adjacent_nodes(item, nodes, connections)
                next_adjacent.extend(new_adjacent)
            adjacent = next_adjacent
        result = {
            "class": "go.GraphLinksModel",
            "copiesArrays": True,
            "copiesArrayObjects": True,
            "nodeDataArray": nodes,
            "linkDataArray": connections,
        }
        return json.dumps(result)


class PortAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "run", "db_value")
    raw_id_fields = ("run",)
    ordering = ("run",)
    search_fields = ("run__id",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PipelineNameAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class OperatorSDKAdmin(AdminAdvancedFiltersMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "version"
    )


admin.site.register(Run, RunAdmin)
admin.site.register(Port, PortAdmin)
admin.site.register(PipelineName, PipelineNameAdmin)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
admin.site.register(OperatorRun, OperatorRunAdmin)
admin.site.register(OperatorTrigger, OperatorTriggerAdmin)
admin.site.register(OperatorSDK, OperatorSDKAdmin)
