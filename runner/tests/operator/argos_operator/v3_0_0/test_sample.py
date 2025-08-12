import json
import os
from datetime import datetime
from pprint import pprint
from uuid import UUID

from django.conf import settings
from django.core.management import call_command
from django.db.models import Prefetch, Q
from django.test import TestCase, override_settings

from file_system.models import File, FileGroup, FileMetadata, FileType, PooledNormal
from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.v3_0_0.bin.files_object import FilesObj
from runner.operator.argos_operator.v3_0_0.bin.sample_igo import SampleIGO
from runner.operator.argos_operator.v3_0_0.bin.sample_metadata import SampleMetadata
from runner.run.processors.file_processor import FileProcessor


class TestSampleIGO(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
        except Exception as e:
            print(f"Error in setUp: {e}")

        self.files = FileRepository.all()

    def test_create_sample_tumor_fastqs(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.fixtures.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        files = FileRepository.filter(queryset=self.files, metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})

        samples = dict()  # might not be necessary
        file_list = dict()
        for f in files:
            # sample = dict()
            # sample["id"] = f.file.id
            # sample["path"] = f.file.path
            # sample["file_name"] = f.file.file_name
            # sample["file_type"] = f.file.file_type
            #            sample["metadata"] = f.metadata
            sample_name = f.metadata["ciTag"]
            if sample_name not in file_list:
                #    samples[sample_name] = list()
                file_list[sample_name] = list()
            # samples[sample_name].append(sample)
            file_list[sample_name].append(f)

        for sample_name in file_list:
            sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")

        for sample_file in sample_igo.sample_files:
            pprint(sample_file)

        # TODO check samples are built properly
        self.assertEqual(len(file_list), 4)

    def test_create_sample_clinical_bams(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.fixtures.json")  # TODO: use a bam fixture
        call_command("loaddata", test_files_fixture, verbosity=0)

        files = FileRepository.filter(queryset=self.files, metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})

        file_list = dict()
        for f in files:
            sample_name = f.metadata["ciTag"]
            if sample_name not in file_list:
                file_list[sample_name] = list()
            file_list[sample_name].append(f)

            # for sample_name in file_list:
            # sample_igo = SampleIGO(sample_name, file_list[sample_name], "bam")
            # pprint(sample_igo.data)

        # TODO check samples are built properly


#        self.assertEqual(len(file_list), 1)
