# Generated by Django 2.2.24 on 2022-02-18 15:06

import copy
from django.db import migrations
from file_system.repository.file_repository import FileRepository


def migrate_metadata(apps, schema_editor):
    files = FileRepository.all()
    for f in files:
        f.metadata


def _remap_metadata(metadata):
    new_metadata = copy.deepcopy(metadata)
    new_metadata["datasource"] = "igo"
    new_metadata["cmoInfoIgoId"] = new_metadata["sampleId"]
    new_metadata["sampleAliases"] = [
        {"namespace": "igoId", "value": new_metadata["sampleId"]},
        {"namespace": "investigatorId", "value": new_metadata["investigatorSampleId"]},
    ]
    new_metadata["primaryId"] = new_metadata.pop("sampleId")
    new_metadata["genePanel"] = new_metadata.pop("recipe")
    new_metadata["igoProjectId"] = new_metadata["requestId"].split("_")[0]
    new_metadata["igoRequestId"] = new_metadata.pop("requestId")
    new_metadata["oncotreeCode"] = new_metadata.pop("oncoTreeCode")
    new_metadata["patientAliases"] = ({"namespace": "cmoId", "value": new_metadata["patientId"]},)
    new_metadata["sampleType"] = new_metadata.pop("sampleClass")
    new_metadata["sampleClass"] = new_metadata.pop("specimenType")


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0028_request_delivery_date"),
    ]

    operations = []