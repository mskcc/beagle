from django.contrib import admin, messages
from django.urls import reverse
from django.utils.translation import ngettext
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger, RunStatus
from lib.admin import link_relation, progress_bar, pretty_python_exception
from rangefilter.filter import DateTimeRangeFilter
from django.utils.html import format_html
from beagle.settings import RIDGEBACK_URL, BEAGLE_URL
from runner.tasks import abort_job_task
import requests


class PipelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'version', 'default', 'output_directory', link_relation("operator"))

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('github', 'version')
        else:
            return []

class AppFilter(admin.SimpleListFilter):
    title = 'App'
    parameter_name = 'app'

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
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        # TODO support range in status count
        filters = {k:v for (k, v) in request.GET.items() if "range" not in k and "status" not in k
                   and "q" not in k and "p" not in k and "o" not in k}

        qs = model_admin.get_queryset(request).filter(**filters)
        if request.GET.get("q"):
            qs, _use_distinct = model_admin.get_search_results(request, qs, request.GET.get("q"))
        return [(status.value, "%s (%s)" % (status.name, qs.filter(status=status.value).count())) for status in RunStatus]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

def abort_run(modeladmin, request, queryset):
    jobs = list(queryset.values_list("id", flat=True))
    updated = len(jobs)
    abort_job_task.delay(None, jobs)
    modeladmin.message_user(request, ngettext(
        '%d job was submitted to be cancelled',
        '%d jobs were submitted to be cancelled',
        updated,
    ) % updated, messages.SUCCESS)

abort_run.short_description = "Abort Run"

class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', link_relation("app"), link_relation("operator_run"), 'tags',
                    'status', 'link_to_ridgeback', 'created_date', 'finished_date')
    ordering = ('-created_date',)
    list_filter = (('created_date', DateTimeRangeFilter), StatusFilter, AppFilter,)
    search_fields = ('tags__sampleId', 'tags__requestId', 'tags__cmoSampleIds__contains',
                     'operator_run__id')
    readonly_fields = ('samples', 'job_group', 'job_group_notifier', link_relation('operator_run'),
                       link_relation('app'))

    actions = [abort_run]

    def link_to_ridgeback(self, obj):
        if not obj.execution_id:
            return "-"
        return format_html("<a target='_blank' href='{ridgeback_url}/admin/toil_orchestrator/job/{execution_id}'>{execution_id}</a>",
                           execution_id=obj.execution_id, ridgeback_url=RIDGEBACK_URL)
    link_to_ridgeback.short_description = "Execution ID (Ridgeback)"


class OperatorRunAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("operator"), 'first_run', 'status', 'run_count', progress_bar('percent_runs_succeeded'),
                    progress_bar('percent_runs_finished'), 'created_date',)
    ordering = ('-created_date',)

    def run_count(self, obj):
        return obj.runs.count()

    def first_run(self, obj):
        run = obj.runs.first()
        if run:
            url = reverse('admin:{}_{}_change'.format(obj._meta.app_label, "run"),
                          args=(run.pk,))
            return format_html("<a href='{url}'>{name}</a>",
                           url=url, name=run.name)

    def has_change_permission(self, request, obj=None):
        return False


class OperatorTriggerAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("from_operator"), link_relation("to_operator"), 'aggregate_condition')


class PortAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'run', 'db_value')
    raw_id_fields = ("run",)
    ordering = ('run',)
    search_fields = ('run__id',)

    def has_add_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(Run, RunAdmin)
admin.site.register(Port, PortAdmin)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
admin.site.register(OperatorRun, OperatorRunAdmin)
admin.site.register(OperatorTrigger, OperatorTriggerAdmin)
