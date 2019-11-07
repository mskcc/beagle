from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents


class PipelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'github', 'version', 'output_directory')


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'app', 'status', 'execution_id', 'created_date')


admin.site.register(Run, RunAdmin)
admin.site.register(Port)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
