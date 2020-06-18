from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger, PortType
from lib.admin import link_relation, progress_bar, pretty_python_exception


class PipelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'github', 'version', 'output_directory', link_relation("operator"))


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', link_relation("app"), link_relation("operator_run"), 'tags', 'status', 'execution_id', 'created_date', 'notify_for_outputs')
    ordering = ('-created_date',)


class OperatorRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', progress_bar('percent_runs_succeeded'), progress_bar('percent_runs_finished'))
    read_only = ('message')


class OperatorTriggerAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("from_operator"), link_relation("to_operator"), 'aggregate_condition')


class PortTypeFilter(SimpleListFilter):
    title = 'Type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return [(member.value, name) for name, member in PortType.__members__.items()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(port_type =self.value())
        return queryset


class PortAdmin(admin.ModelAdmin):
    list_display = ('id', 'port_type', 'name', 'run', 'db_value')
    raw_id_fields = ("run",)
    ordering = ('run',)
    search_fields = ('run__id', 'run__job_group')
    autocomplete_fields = ['files']
    list_filter = (PortTypeFilter,)

admin.site.register(Run, RunAdmin)
admin.site.register(Port, PortAdmin)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
admin.site.register(OperatorRun, OperatorRunAdmin)
admin.site.register(OperatorTrigger, OperatorTriggerAdmin)
