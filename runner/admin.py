from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents


class PipelineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'github', 'version', 'output_directory')


admin.site.register(Run)
admin.site.register(Port)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(ExecutionEvents)
