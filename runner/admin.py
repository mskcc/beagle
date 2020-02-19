from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents, OperatorRun, OperatorTrigger
from lib.admin import link_relation, progress_bar

class PipelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'github', 'version', 'output_directory', link_relation("operator"))

class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', link_relation("operator_run"), 'tags', 'status', 'execution_id', 'created_date')
    ordering = ('-created_date',)

class OperatorRunAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("trigger"), 'status', progress_bar('percent_complete'))

class OperatorTriggerAdmin(admin.ModelAdmin):
    list_display = ('id', link_relation("from_operator"), link_relation("to_operator"), 'condition')

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
