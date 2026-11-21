from django.contrib import admin
from django.contrib.admin import ModelAdmin
from advanced_filters.admin import AdminAdvancedFiltersMixin
from .models import Operator


class OperatorAdmin(AdminAdvancedFiltersMixin, ModelAdmin):
    list_display = ("id", "name", "type", "class_name", "version", "status", "docker_image_tag", "active")
    list_filter = ("active", "type", "status")
    advanced_filter_fields = ("active", "type", "status")
    search_fields = ("name", "class_name", "version")


admin.site.register(Operator, OperatorAdmin)
