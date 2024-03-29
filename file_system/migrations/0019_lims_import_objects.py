# Generated by Django 2.2.11 on 2020-09-08 21:01

import copy
from django.db import migrations


def add_import_metadata(apps, schema_editor):
    FileMetadata = apps.get_model("file_system", "FileMetadata")
    FileGroup = apps.get_model("file_system", "FileGroup")
    ImportMetadata = apps.get_model("file_system", "ImportMetadata")

    try:
        fg = FileGroup.objects.get(name="LIMS")
    except FileGroup.DoesNotExist:
        return
    metadatas = FileMetadata.objects.filter(file__file_group=fg, version=0)

    for m in metadatas:
        lims_metadata = _revert_metadata(m.metadata)
        if not ImportMetadata.objects.filter(file=m.file):
            ImportMetadata.objects.create(file=m.file, metadata=lims_metadata)


def remove_import_metadata(apps, schema_editor):
    ImportMetadata = apps.get_model("file_system", "ImportMetadata")
    ImportMetadata.objects.all().delete()


def _revert_metadata(metadata):
    lims_metadata = copy.deepcopy(metadata)
    lims_metadata["cmoSampleName"] = lims_metadata.pop("sampleName", None)
    lims_metadata["sampleName"] = lims_metadata.pop("externalSampleId", None)
    lims_metadata["libraryIgoId"] = lims_metadata.pop("libraryId", None)
    lims_metadata["cmoPatientId"] = lims_metadata.pop("patientId", None)
    lims_metadata.pop("platform")
    lims_metadata["cmoSampleClass"] = lims_metadata.pop("sampleClass", None)
    lims_metadata["igoId"] = lims_metadata.pop("sampleId", None)
    lims_metadata.pop("sequencingCenter", None)
    return lims_metadata


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0018_importmetadata"),
    ]

    operations = [
        migrations.RunPython(add_import_metadata, reverse_code=remove_import_metadata),
    ]
