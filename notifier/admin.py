from django.contrib import admin
from .models import JobGroup, Notifier, JobGroupNotifier


class JobGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'jira_id')
    ordering = ('-created_date',)


class JobGroupNotifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'jira_id', 'job_group', 'notifier_type', 'created_date')
    ordering = ('-created_date',)


class NotifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'notifier_type', 'default', 'created_date')


admin.site.register(JobGroup, JobGroupAdmin)
admin.site.register(Notifier, NotifierAdmin)
admin.site.register(JobGroupNotifier, JobGroupNotifierAdmin)
