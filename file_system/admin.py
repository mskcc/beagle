import os
from django import forms
from django.contrib import admin
from import_export.admin import ExportActionMixin
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField
from django.utils.safestring import mark_safe
from django.forms import Textarea
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
    PooledNormal,
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


class PooledNormalsAdminForm(forms.ModelForm):
    def clean_machine(self):
        if not self.cleaned_data["machine"].islower():
            raise ValidationError("Machine needs to be lowercase")
        return self.cleaned_data["machine"]

    def clean_gene_panel(self):
        if not self.cleaned_data["gene_panel"].islower():
            raise ValidationError("Gene Panel/Recipe needs to be lowercase")
        return self.cleaned_data["gene_panel"]

    def clean_bait_set(self):
        if not self.cleaned_data["bait_set"].islower():
            raise ValidationError("BaitSet needs to be lowercase")
        return self.cleaned_data["bait_set"]

    def clean_pooled_normals_paths(self):
        pooled_normals_paths = self.cleaned_data["pooled_normals_paths"]
        for pooled_normal_path in pooled_normals_paths:
            if not os.path.exists(pooled_normal_path):
                raise ValidationError(f"File {pooled_normal_path} does not exist; will not add.")
        return self.cleaned_data["pooled_normals_paths"]


class PooledNormalsAdmin(admin.ModelAdmin):
    form = PooledNormalsAdminForm
    formfield_overrides = {
        ArrayField: {"widget": Textarea(attrs={"rows": 3, "cols": 40})},
    }
    list_display = (
        "machine",
        "gene_panel",
        "bait_set",
        "preservation_type",
        "formatted_run_date",
        "formatted_pooled_normals_paths",
    )

    def formatted_run_date(self, obj):
        return obj.run_date.strftime("%m-%d-%Y")

    formatted_run_date.short_description = "Run Date"

    def formatted_pooled_normals_paths(self, obj):
        if obj.pooled_normals_paths:
            return mark_safe("<br>".join(obj.pooled_normals_paths))

    formatted_pooled_normals_paths.short_description = "Pooled Normals Paths"


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
admin.site.register(PooledNormal, PooledNormalsAdmin)
