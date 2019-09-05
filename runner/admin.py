from django.contrib import admin
from .models import Pipeline, Run, Port, ExecutionEvents


admin.site.register(Run)
admin.site.register(Port)
admin.site.register(Pipeline)
admin.site.register(ExecutionEvents)
