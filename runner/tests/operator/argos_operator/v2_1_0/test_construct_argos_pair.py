"""
Test for constructing Argos pair and jobs
"""
import os
import json
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from file_system.models import File
from runner.operator.argos_operator.v2_1_0.bin.make_sample import build_sample
from runner.operator.argos_operator.v2_1_0.construct_argos_pair import construct_argos_jobs


class TestConstructPair(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        os.environ["TMPDIR"] = ""

    def test_construct_argos_jobs1(self):
        """
        Test that Argos jobs are correctly created
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        request_id_metadata_key = settings.REQUEST_ID_METADATA_KEY
        igo_complete_metadata_key = settings.IGO_COMPLETE_METADATA_KEY

        files = File.objects.filter(
            **{
                "filemetadata__metadata__{}".format(request_id_metadata_key): "10075_D",
                "filemetadata__metadata__{}".format(igo_complete_metadata_key): True,
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

        argos_inputs, error_samples = construct_argos_jobs(samples)
        expected_inputs = json.load(
            open(os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.argos_1_7_0.input.json"))
        )

        print("Running test_construct_argos_jobs1")
        self.assertTrue(argos_inputs == expected_inputs)

    def test_construct_argos_jobs_pdx(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.fixtures.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        request_id_metadata_key = settings.REQUEST_ID_METADATA_KEY
        igo_complete_metadata_key = settings.IGO_COMPLETE_METADATA_KEY

        files = File.objects.filter(
            **{
                "filemetadata__metadata__{}".format(request_id_metadata_key): "08944_B",
                "filemetadata__metadata__{}".format(igo_complete_metadata_key): True,
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

        igo_id_group = dict()
        for sample in data:
            igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        argos_inputs, error_samples = construct_argos_jobs(samples)
        expected_inputs = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "08944_B.argos.input.json")))
        print("Running test_construct_argos_jobs_pdx")
        self.assertTrue(argos_inputs == expected_inputs)

    def test_construct_argos_jobs_bam_pdx(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "16342_B.fixtures_pdx.json")
        bam_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "argos_pdx.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        call_command("loaddata", bam_fixture, verbosity=0)

        request_id_metadata_key = settings.REQUEST_ID_METADATA_KEY
        igo_complete_metadata_key = settings.IGO_COMPLETE_METADATA_KEY

        files = File.objects.filter(
            **{
                "filemetadata__metadata__{}".format(request_id_metadata_key): "16342_B",
                "filemetadata__metadata__{}".format(igo_complete_metadata_key): True,
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

        igo_id_group = dict()
        for sample in data:
            igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        argos_inputs, error_samples = construct_argos_jobs(samples)
        expected_inputs = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "argos_pdx.inputs.json")))
        print("Running test_construct_argos_jobs_pdx")
        self.assertTrue(argos_inputs == expected_inputs)

    def test_construct_argos_jobs_bam_non_pdx(self):
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "16342_B.fixtures_non_pdx.json")
        bam_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "argos_pdx.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        call_command("loaddata", bam_fixture, verbosity=0)

        request_id_metadata_key = settings.REQUEST_ID_METADATA_KEY
        igo_complete_metadata_key = settings.IGO_COMPLETE_METADATA_KEY

        files = File.objects.filter(
            **{
                "filemetadata__metadata__{}".format(request_id_metadata_key): "16342_B",
                "filemetadata__metadata__{}".format(igo_complete_metadata_key): True,
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

        igo_id_group = dict()
        for sample in data:
            igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        argos_inputs, error_samples = construct_argos_jobs(samples)
        expected_inputs = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "argos_non_pdx.inputs.json")))
        print("Running test_construct_argos_jobs_bam_non_pdx")
        self.assertTrue(argos_inputs == expected_inputs)
