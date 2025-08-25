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
from runner.operator.argos_operator.v3_0_0.bin.pair_object import PairObj
from runner.operator.argos_operator.v3_0_0.bin.sample_igo import SampleIGO


class TestPairsObj(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
        except Exception as e:
            print(f"Error in setUp: {e}")

        self.files = FileRepository.all()

    def test_create_pairs(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.fixtures.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        files = FileRepository.filter(queryset=self.files, metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})

        samples = dict()
        file_list = dict()
        for f in files:
            sample_name = f.metadata["ciTag"]
            if sample_name not in file_list:
                file_list[sample_name] = list()
            file_list[sample_name].append(f)

        for sample_name in file_list:
            sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")
            samples[sample_name] = sample_igo

        for sample_file in sample_igo.sample_files:
            pprint(sample_file)

        # TODO check samples are built properly
        self.assertEqual(len(file_list), 4)

        for sample_name in samples:
            pprint(sample_name + " " + samples[sample_name].sample_type)

        tumor = samples["s_C_MP76JR_X001_d"]
        normal = samples["s_C_MP76JR_N001_d"]

        pair_obj = PairObj(tumor, normal)
        pprint(pair_obj)
