from django.contrib import admin
from .models import SampleProviderJob, FileProviderJob, CleanupFileJob, FileProviderStatus


@admin.register(SampleProviderJob)
class SampleProviderJobAdmin(admin.ModelAdmin):
    list_display = (
        "sample_id",
        "status",
        "completed_files",
        "total_files",
        "progress_percentage",
        "created_date",
        "modified_date",
    )
    list_filter = ("status", "created_date", "modified_date")
    search_fields = ("sample_id",)
    readonly_fields = ("id", "created_date", "modified_date")

    def progress_percentage(self, obj):
        if obj.total_files == 0:
            return "0%"
        return f"{(obj.completed_files / obj.total_files * 100):.1f}%"

    progress_percentage.short_description = "Progress"


@admin.register(FileProviderJob)
class FileProviderJobAdmin(admin.ModelAdmin):
    list_display = (
        "file_object",
        "status",
        "original_path_short",
        "staged_path_short",
        "created_date",
        "modified_date",
    )
    list_filter = ("status", "created_date", "modified_date")
    search_fields = ("original_path", "staged_path", "file_object__file_name")
    readonly_fields = ("id", "created_date", "modified_date")
    raw_id_fields = ("file_object",)

    def original_path_short(self, obj):
        return obj.original_path[-50:] if len(obj.original_path) > 50 else obj.original_path

    original_path_short.short_description = "Original Path"

    def staged_path_short(self, obj):
        return obj.staged_path[-50:] if len(obj.staged_path) > 50 else obj.staged_path

    staged_path_short.short_description = "Staged Path"


@admin.register(CleanupFileJob)
class CleanupFileJobAdmin(admin.ModelAdmin):
    list_display = (
        "file_object",
        "status",
        "cleanup_date",
        "days_until_cleanup",
        "original_path_short",
        "created_date",
    )
    list_filter = ("status", "cleanup_date", "created_date")
    search_fields = ("original_path", "file_object__file_name")
    readonly_fields = ("id", "created_date", "modified_date")
    raw_id_fields = ("file_object",)
    date_hierarchy = "cleanup_date"

    def original_path_short(self, obj):
        return obj.original_path[-50:] if len(obj.original_path) > 50 else obj.original_path

    original_path_short.short_description = "Original Path"

    def days_until_cleanup(self, obj):
        from datetime import date

        delta = obj.cleanup_date - date.today()
        days = delta.days
        if days < 0:
            return f"Overdue by {abs(days)} days"
        elif days == 0:
            return "Today"
        else:
            return f"In {days} days"

    days_until_cleanup.short_description = "Cleanup In"
