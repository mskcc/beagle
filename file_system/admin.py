from django import forms
from django.contrib import admin
from import_export.admin import ExportActionMixin
from django.core.exceptions import ValidationError
from .models import (
    Storage,
    File,
    FileType,
    FileMetadata,
    FileGroup,
    FileGroupMetadata,
    FileRunMap,
    ImportMetadata,
    Sample,
    Patient,
    Request,
    FileExtension,
    MachineRunMode,
)


class FileGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "default", "owner")
    search_fields = ("name", "owner")


class FileAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ("id", "file_name", "file_group", "size", "created_date")
    search_fields = ["file_name"]


class SampleAdmin(admin.ModelAdmin):
    list_display = ("id", "sample_id", "sample_name", "cmo_sample_name", "redact")
    search_fields = ["sample_id"]


class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request_id",
    )
    search_fields = ["request_id"]


class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient_id",
    )
    search_fields = ["patient_id"]


class FileRunMapAdmin(admin.ModelAdmin):
    list_display = ("file", "run")


class FileMetadataAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ("file", "version", "metadata", "created_date")
    autocomplete_fields = ["file"]
    search_fields = ("id", "file__id", "metadata__igoRequestId", "metadata__cmoSampleName")


class ImportMetadataAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ("file",)
    search_fields = ("file__id",)


class MachineRunModeAdminForm(forms.ModelForm):
    def clean_machine_name(self):
        if not self.cleaned_data["machine_name"].islower():
            raise ValidationError("Machine name needs to be lowercase")
        return self.cleaned_data["machine_name"]

    def clean_machine_class(self):
        if not self.cleaned_data["machine_class"].islower():
            raise ValidationError("Machine class needs to be lowercase")
        return self.cleaned_data["machine_class"]


class MachineRunModeAdmin(admin.ModelAdmin):
    form = MachineRunModeAdminForm
    list_display = ("machine_name", "machine_class", "machine_type")


admin.site.register(File, FileAdmin)
admin.site.register(Storage)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(FileGroup, FileGroupAdmin)
admin.site.register(FileType)
admin.site.register(FileExtension)
admin.site.register(FileMetadata, FileMetadataAdmin)
admin.site.register(ImportMetadata, ImportMetadataAdmin)
admin.site.register(FileGroupMetadata)
admin.site.register(FileRunMap, FileRunMapAdmin)
admin.site.register(MachineRunMode, MachineRunModeAdmin)
