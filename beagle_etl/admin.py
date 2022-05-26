import os
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin, SimpleListFilter
from django.utils.safestring import mark_safe
from .models import (
    Job,
    JobStatus,
    Operator,
    ETLConfiguration,
    SMILEMessage,
    RequestCallbackJob,
    NormalizerModel,
    ValidatorModel,
)
from advanced_filters.admin import AdminAdvancedFiltersMixin
from lib.admin import pretty_json
from beagle_etl.tasks import process_smile_message


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
    title = "Recipe"
    parameter_name = settings.RECIPE_METADATA_KEY

    def lookups(self, request, model_admin):
        options = set()

        for o in Operator.objects.values("recipes"):
            for recipe in o["recipes"]:
                options.add((recipe, recipe))
        return options

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(args__request_metadata__genePanel=self.value())
        return queryset


class JobAdmin(ModelAdmin):
    list_display = (
        "id",
        "get_short_run",
        "retry_count",
        pretty_json("args"),
        "children",
        "status",
        "created_date",
        "lock",
        pretty_json("message"),
    )
    search_fields = ("id", "args__sample_id")
    readonly_fields = ("message",)
    actions = (restart,)
    ordering = ("-created_date",)
    list_filter = (RecipeFilter,)

    def get_short_run(self, obj):
        if obj.run:
            (_, run) = os.path.splitext(obj.run)
            return mark_safe("<span title='%s'>%s</span>" % (obj.run, run[1:]))
        else:
            return "--"

    get_short_run.short_description = "Run"


class OperatorAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_display = ("id", "slug", "class_name", "version", "recipes", "active")
    list_filter = ("active",)
    advanced_filter_fields = ("active",)


class AssayAdmin(ModelAdmin):
    list_display = ("redelivery", "all_recipes", "disabled_recipes")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def action_process_messages(modeladmin, request, queryset):
    for job in queryset:
        process_smile_message(job)


action_process_messages.short_description = "Process SMILE messages"


class SMILEMessagesAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_filter = ("request_id", "topic", "status")
    actions = (action_process_messages,)
    advanced_filter_fields = ("request_id", "topic", "status")
    ordering = ("-created_date",)
    list_display = ("created_date", "request_id", "topic", "status")


class RequestCallbackJobAdmin(ModelAdmin):
    list_display = ("created_date", "request_id", "recipe", "status")


class NormalizerAdmin(ModelAdmin):
    list_display = (
        "condition",
        "normalizer",
    )


class ValidatorAdmin(ModelAdmin):
    list_display = ("name",)


admin.site.register(Job, JobAdmin)
admin.site.register(Operator, OperatorAdmin)
admin.site.register(ETLConfiguration, AssayAdmin)
admin.site.register(SMILEMessage, SMILEMessagesAdmin)
admin.site.register(RequestCallbackJob, RequestCallbackJobAdmin)
admin.site.register(NormalizerModel, NormalizerAdmin)
admin.site.register(ValidatorModel, ValidatorAdmin)
