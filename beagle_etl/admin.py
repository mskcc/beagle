from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Job, JobStatus, Operator
from lib.admin import pretty_python_exception, pretty_json


def restart(modeladmin, request, queryset):
    for job in queryset:
        for child in job.children:
            child_job = Job.objects.get(id=child)
            if child_job.status == JobStatus.FAILED:
                child_job.status = JobStatus.CREATED
                child_job.retry_count = 0
                child_job.save()
        job.status = JobStatus.CREATED
        job.retry_count = 0
        job.save()

restart.short_description = "Restart"


class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'run', 'retry_count', pretty_json('args'), 'children', 'status', 'created_date', 'lock', pretty_python_exception('message'))
    search_fields = ('id', 'args__sample_id')
    readonly_fields = ('message',)
    actions = (restart,)
    ordering = ('-created_date',)

class OperatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'class_name', 'recipes', 'active')


admin.site.register(Job, JobAdmin)
admin.site.register(Operator, OperatorAdmin)
