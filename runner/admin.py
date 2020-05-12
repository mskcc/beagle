from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger
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
