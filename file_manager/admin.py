from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.conf import settings
from celery import chord
from .models import SampleProviderJob, FileProviderJob, CleanupFileJob, FileProviderStatus
from file_manager.file_manager import FileManager


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

    change_list_template = "admin/file_manager/sampleproviderjob_changelist.html"

    def has_add_permission(self, request):
        """Remove 'Add' button - users should use 'Stage Sample Files' instead"""
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stage-sample/', self.admin_site.admin_view(self.stage_sample_view), name='file_manager_stage_sample'),
        ]
        return custom_urls + urls

    def stage_sample_view(self, request):
        """Admin view to manually stage files for a sample"""
        if request.method == 'POST':
            sample_id = request.POST.get('sample_id', '').strip()
            file_group = request.POST.get('file_group', settings.IMPORT_FILE_GROUP)

            if not sample_id:
                messages.error(request, 'Sample ID is required')
                return render(request, 'admin/file_manager/stage_sample.html', {
                    'title': 'Stage Sample Files',
                    'default_file_group': settings.IMPORT_FILE_GROUP,
                })

            try:
                file_manager = FileManager(file_group=file_group)
                sample_job, task_sigs = file_manager.stage_sample(sample_id)

                if sample_job.total_files > 0:
                    # Execute tasks
                    if task_sigs:
                        # Execute each task individually (no chord needed in admin)
                        for task in task_sigs:
                            task.delay()
                        messages.success(
                            request,
                            f'Staging {len(task_sigs)} files for sample {sample_id}. '
                            f'Job ID: {sample_job.id}'
                        )
                    else:
                        messages.warning(
                            request,
                            f'Sample {sample_id} has {sample_job.total_files} files to stage, '
                            f'but no tasks were created (files may already be staging)'
                        )
                else:
                    messages.info(request, f'No files need staging for sample {sample_id}')

                # Redirect to the job detail page
                return redirect('admin:file_manager_sampleproviderjob_change', sample_job.id)

            except Exception as e:
                import traceback
                messages.error(request, f'Error staging files: {str(e)}\n{traceback.format_exc()}')

        return render(request, 'admin/file_manager/stage_sample.html', {
            'title': 'Stage Sample Files',
            'default_file_group': settings.IMPORT_FILE_GROUP,
        })

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
