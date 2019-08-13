from django.contrib import admin
from .models import Pipeline, Run


admin.site.register(Run)
admin.site.register(Pipeline)
