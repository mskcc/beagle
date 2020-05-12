import os
from django.contrib import admin
from django.contrib.admin import ModelAdmin, SimpleListFilter
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

class RecipeFilter(SimpleListFilter):
    title = 'Recipe'
    parameter_name = 'recipe'

    def lookups(self, request, model_admin):
        options = set()

        for o in Operator.objects.values("recipes"):
            for recipe in o["recipes"]:
                options.add((recipe, recipe))
        return options

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(args__request_metadata__recipe=self.value())
        return queryset


class JobAdmin(ModelAdmin):
    list_display = ('id', 'get_short_run', 'retry_count',
                    pretty_json('args'),
                    'children',
                    'status',
                    'created_date',
                    'lock',
                    pretty_json('message'))
    search_fields = ('id', 'args__sample_id')
    readonly_fields = ('message',)
    actions = (restart,)
    ordering = ('-created_date',)
    list_filter = (RecipeFilter, )

    def get_short_run(self, obj):
        if obj.run:
            (_, run) = os.path.splitext(obj.run)
            return mark_safe("<span title='%s'>%s</span>" % (obj.run, run[1:]))
        else:
            return '--'

    get_short_run.short_description = 'Run'

class OperatorAdmin(ModelAdmin):
    list_display = ('id', 'class_name', 'recipes', 'active')


admin.site.register(Job, JobAdmin)
admin.site.register(Operator, OperatorAdmin)
