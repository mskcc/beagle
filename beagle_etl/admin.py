from django.contrib import admin
from django.contrib.admin import ModelAdmin
from lib.admin import link_relation
from .models import (
    Operator,
    ETLConfiguration,
    SMILEMessage,
    RequestCallbackJob,
    NormalizerModel,
    ValidatorModel,
    SkipProject,
    CopyFileTask,
)
from advanced_filters.admin import AdminAdvancedFiltersMixin


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


class SMILEMessagesAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_filter = ("request_id", "topic", "status")
    advanced_filter_fields = ("request_id", "topic", "status")
    ordering = ("-created_date",)
    list_display = ("created_date", "request_id", "topic", "status")


class RequestCallbackJobAdmin(ModelAdmin):
    list_display = ("id", link_relation("smile_message"), "request_id", "recipe", "created_date", "status")
    ordering = ("-created_date",)


class NormalizerAdmin(ModelAdmin):
    list_display = (
        "condition",
        "normalizer",
    )


class ValidatorAdmin(ModelAdmin):
    list_display = ("name",)


class SkipProjectAdmin(ModelAdmin):
    list_display = ("skip_projects",)


class CopyFileTaskAdmin(ModelAdmin):
    list_display = (
        "id",
        "source",
        "destination",
        link_relation("smile_message"),
        "created_date",
        "status",
    )
    ordering = ("-created_date",)


admin.site.register(Operator, OperatorAdmin)
admin.site.register(ETLConfiguration, AssayAdmin)
admin.site.register(SMILEMessage, SMILEMessagesAdmin)
admin.site.register(RequestCallbackJob, RequestCallbackJobAdmin)
admin.site.register(NormalizerModel, NormalizerAdmin)
admin.site.register(ValidatorModel, ValidatorAdmin)
admin.site.register(SkipProject, SkipProjectAdmin)
admin.site.register(CopyFileTask, CopyFileTaskAdmin)
