from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.conf import settings
from lib.admin import link_relation
from .models import (
    Operator,
    ETLConfiguration,
    SMILEMessage,
    RequestCallbackJob,
)
from .jobs.metadb_jobs import new_request
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
    actions = ["force_import"]

    @admin.action(description="Force import selected SMILE messages (skip validation)")
    def force_import(self, request, queryset):
        for message in queryset.filter(topic=settings.METADB_NATS_NEW_REQUEST):
            new_request.delay(str(message.id), force_import=True)
        self.message_user(request, f"Force import triggered for {queryset.count()} message(s).")


class RequestCallbackJobAdmin(ModelAdmin):
    list_display = ("id", link_relation("smile_message"), "request_id", "recipe", "created_date", "status")
    ordering = ("-created_date",)


admin.site.register(Operator, OperatorAdmin)
admin.site.register(ETLConfiguration, AssayAdmin)
admin.site.register(SMILEMessage, SMILEMessagesAdmin)
admin.site.register(RequestCallbackJob, RequestCallbackJobAdmin)
