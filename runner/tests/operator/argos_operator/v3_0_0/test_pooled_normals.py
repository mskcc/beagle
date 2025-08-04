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
from runner.operator.argos_operator.v3_0_0.bin.sample_metadata import SampleMetadata
from runner.operator.argos_operator.v3_0_0.bin.sample_pooled_normal import SamplePooledNormal


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

    def test_sample_pooled_normal(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.fixtures.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        test_sample_pooled_normal = SamplePooledNormal()
