import json
import os
from datetime import datetime
from pprint import pprint
from uuid import UUID

from django.conf import settings
from django.core.management import call_command
from django.db.models import Prefetch, Q
from django.test import TestCase, override_settings

from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.v3_0_0.bin.helpers import spoof_barcode
from runner.operator.argos_operator.v3_0_0.bin.sample_dmp import SampleDMP


class TestSampleDMP(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "DMP_data.json",
    ]

    def setUp(self):
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
            call_command("loaddata", "DMP_data.json")
        except Exception as e:
            print(f"Error in setUp: {e}")

        self.files = FileRepository.all()

    def test_create_sample_clinical_bams(self):
        from pprint import pprint

        files = FileRepository.filter(queryset=self.files, metadata={"patient__cmo": "ALLANT"})

        bam_f = files.first()
        bam_meta = bam_f.metadata
        metadata = {
            settings.CMO_SAMPLE_NAME_METADATA_KEY: "test_sample_name",
            settings.REQUEST_ID_METADATA_KEY: "test_request_id",
            settings.SAMPLE_CLASS_METADATA_KEY: "test_sample_class",
            settings.PATIENT_ID_METADATA_KEY: bam_meta["patient"]["cmo"],
            settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Tumor",
            settings.CMO_SAMPLE_TAG_METADATA_KEY: "test_sample_citag",
            settings.LIBRARY_ID_METADATA_KEY: "test_library_id",
            settings.BAITSET_METADATA_KEY: bam_meta["cmo_assay"],
            "sequencingCenter": "MSKCC",
            "platform": "Illumina",
            "barcodeIndex": spoof_barcode(bam_f.file.path),
            "flowCellId": "test_fcid",
        }

        pprint(metadata)

        dmp_sample = SampleDMP(metadata)
        pprint(dmp_sample)
        pprint(dmp_sample.metadata)
