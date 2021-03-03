from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger, RunStatus
from lib.admin import link_relation, progress_bar, pretty_python_exception
from rangefilter.filter import DateTimeRangeFilter

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
        # TODO support range/q
        filters = {k:v for (k, v) in request.GET.items() if "range" not in k and "status" not in k
                   and "q" not in k and "p" not in k}
        qs = model_admin.get_queryset(request).filter(**filters)
        return [(status.value, "%s (%s)" % (status.name, qs.filter(status=status.value).count())) for status in RunStatus]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', link_relation("app"), link_relation("operator_run"), 'tags', 'status', 'execution_id', 'created_date', 'notify_for_outputs')
    ordering = ('-created_date',)
    list_filter = (('created_date', DateTimeRangeFilter), StatusFilter, AppFilter,)
    search_fields = ('tags__sampleId', 'tags__requestId', 'tags__cmoSampleIds__contains')
    readonly_fields = ('samples', 'job_group', 'job_group_notifier', 'operator_run', 'app')


class OperatorRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', progress_bar('percent_runs_succeeded'), progress_bar('percent_runs_finished'))
    def has_change_permission(self, request, obj=None):
        return False


class OperatorTriggerAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("from_operator"), link_relation("to_operator"), 'aggregate_condition')


class PortAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'run', 'db_value')
    raw_id_fields = ("run",)
    ordering = ('run',)
    search_fields = ('run__id',)


admin.site.register(Run, RunAdmin)
admin.site.register(Port, PortAdmin)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
admin.site.register(OperatorRun, OperatorRunAdmin)
admin.site.register(OperatorTrigger, OperatorTriggerAdmin)
