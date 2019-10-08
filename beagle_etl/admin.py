from django.contrib import admin
from .models import Job


class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'run', 'retry_count', 'args', 'children', 'status', 'message', 'created_date', 'lock')
    search_fields = ('id', 'args__sample_id')

admin.site.register(Job, JobAdmin)
