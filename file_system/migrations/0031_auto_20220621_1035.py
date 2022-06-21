# Generated by Django 2.2.24 on 2022-06-21 14:35

import copy
from django.db import migrations
from file_system.repository.file_repository import FileRepository


def migrate_metadata(apps, schema_editor):
    files = FileRepository.all()
    for f in files:
        f.metadata = _remap_metadata(f.metadata)
        f.save()


def _remap_metadata(metadata):
    new_metadata = copy.deepcopy(metadata)
    if "igocomplete" in new_metadata:
        new_metadata["igoComplete"] = new_metadata.pop("igocomplete")
    return new_metadata


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0030_auto_20220418_1737"),
    ]

    operations = [migrations.RunPython(migrate_metadata)]
