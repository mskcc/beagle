import csv
import json
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from uuid import UUID

from django.conf import settings
from django.core.management import call_command
from django.db.models import Prefetch, Q
from django.test import TestCase, override_settings

from file_system.models import File, FileGroup, FileMetadata, FileType, PooledNormal
from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.v3_0_0.bin.files_object import FilesObj
from runner.operator.argos_operator.v3_0_0.bin.sample_metadata import SampleMetadata
from runner.operator.argos_operator.v3_0_0.bin.sample_pooled_normal import SamplePooledNormal
from runner.run.processors.file_processor import FileProcessor

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
PROJECT_ROOT = SCRIPT_DIR / "operator" / "argos_operator" / "v3_0_0"
CSV_PATH = PROJECT_ROOT / "assets" / "pooled_normals.csv"
POOLED_NORMALS = {}

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_ID_METADATA_KEY,  # primaryId
    settings.PATIENT_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.CMO_SAMPLE_TAG_METADATA_KEY,  # ciTag
    settings.LIBRARY_ID_METADATA_KEY,
    settings.BAITSET_METADATA_KEY,
    settings.PRESERVATION_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
    "runMode",
    "runId",
]


# Taken from sample_pooled_normal.py
def load_csv_to_global_dict(filepath):
    global POOLED_NORMALS  # contains table from assets/pooled_normals.csv
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_name = "_".join([row["bait_set"], row["preservation_type"], row["machine"], "POOLED_NORMAL"])
            sample_name = sample_name.upper()
            POOLED_NORMALS[sample_name] = row
            POOLED_NORMALS[sample_name]["pooled_normals_paths"] = (
                POOLED_NORMALS[sample_name]["pooled_normals_paths"].strip("{}").split(",")
            )


class TestSamplePooledNormal(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
        except Exception as e:
            print(f"Error in setUp: {e}")

        self.files = FileRepository.all()

        pprint(CSV_PATH)
        load_csv_to_global_dict(CSV_PATH)

        pprint(POOLED_NORMALS)

        # need to add file paths to test db
        for sample_name in POOLED_NORMALS:
            d = POOLED_NORMALS[sample_name]
            paths = d["pooled_normals_paths"]

            metadata = dict()
            metadata["baitSet"] = d["bait_set"]
            metadata["genePanel"] = d["gene_panel"]
            metadata["machine"] = d["machine"]
            metadata["preservation"] = d["preservation_type"]
            for path in paths:
                FileProcessor.create_file_obj("file://" + path, 0, "12345", "b6857a56-5d45-451f-b4f6-26148946080f", d)

    def test_sample_pooled_normal(self):

        metadata = dict()
        metadata[settings.PATIENT_ID_METADATA_KEY] = "myPatientId"
        metadata[settings.SAMPLE_CLASS_METADATA_KEY] = "mySampleClass"  # sampleClass
        metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = "myCmoSampleClass"  # sampleType::SMILE
        metadata[settings.LIBRARY_ID_METADATA_KEY] = "myLB"
        metadata[settings.BAITSET_METADATA_KEY] = "IMPACT505_BAITS"
        metadata[settings.PRESERVATION_METADATA_KEY] = "FFPE"
        metadata["sequencingCenter"] = "MSKCC"
        metadata["platform"] = "Illumina"
        metadata["barcodeIndex"] = ""
        metadata["flowCellId"] = "myFlowCellId"
        metadata["runMode"] = "myRunMode"
        metadata["runId"] = "FAUCI2_BLAHBLAH"
        test_sample_pooled_normal = SamplePooledNormal(metadata)

        from pprint import pprint

        for sample_file in test_sample_pooled_normal.sample_files:
            pprint(sample_file)
