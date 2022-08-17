"""
Test for constructing Argos pair and jobs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.alignment_pair_operator.v1_0_0.construct_alignment_argos_inputs import construct_alignment_pair_jobs
from runner.operator.alignment_pair_operator.v1_0_0.bin.make_sample import build_sample
from file_system.models import File
from django.conf import settings
from django.core.management import call_command


class TestConstructPair(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        os.environ["TMPDIR"] = ""

    def test_construct_alignment_pair_jobs1(self):
        """
        Test that alignment argos jobs are correctly created
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        files = File.objects.filter(
            {
                "filemetadata__metadata__{}".format(settings.REQUEST_ID_METADATA_KEY): "10075_D",
                "filemetadata__metadata__{}".format(settings.IGO_COMPLETE_METADATA_KEY): True,
            }
        ).all()
        data = list()
        for file in files:
            sample = dict()
            sample["id"] = file.id
            sample["path"] = file.path
            sample["file_name"] = file.file_name
            sample["metadata"] = file.filemetadata_set.first().metadata
            data.append(sample)
        samples = list()
        # group by igoId
        igo_id_group = dict()
        for sample in data:
            igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        alignment_argos_inputs, error_samples = construct_alignment_pair_jobs(samples)
        expected_inputs = json.load(
            open(os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.argos.input.json"))
        )

        print("Running test_construct_alignment_pair_jobs1")
        print(json.dumps(alignment_argos_inputs))
        print(json.dumps(expected_inputs))
        self.assertTrue(alignment_argos_inputs == expected_inputs)
