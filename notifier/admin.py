from django.contrib import admin
from .models import JobGroup


class JobGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'jira_id')


admin.site.register(JobGroup, JobGroupAdmin)