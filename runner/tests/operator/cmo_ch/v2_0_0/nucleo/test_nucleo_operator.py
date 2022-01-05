import os
import json
from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory
from runner.operator.cmo_ch.v2_0_0.nucleo import construct_sample_inputs, CMOCHNucleoOperator
from django.conf import settings
from django.core.management import call_command


FIXTURES = [
    "fixtures/tests/merge_fastqs/10151_F_13.file.json",
    "fixtures/tests/merge_fastqs/10151_F_13.filemetadata.json",
]

COMMON_FIXTURES = [
    "runner/fixtures/runner.pipeline.json",
    "runner/fixtures/runner.run.json",
    "runner/fixtures/runner.operator_run.json",
    "file_system/fixtures/file_system.filegroup.json",
    "file_system/fixtures/file_system.filetype.json",
    "file_system/fixtures/file_system.storage.json",
    "beagle_etl/fixtures/beagle_etl.operator.json",
]


class TestCMOCHNucleoOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_cmoch_nucleo_operator(self):
        """
        Test that an CMOCH Nucleo operator instance can be created and validated
        """
        operator_files_count = 4
        self.assertEqual(len(File.objects.all()), operator_files_count)
        self.assertEqual(len(FileMetadata.objects.all()), operator_files_count)

        request_id = "10151_F"

        operator_model = Operator.objects.get(id=14)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "279b1691-7f43-4c1d-80c0-fae1453cc8a6")
        self.assertEqual(str(operator.model), "CMOCHNucleoOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job.is_valid(), True)
            # Ensure at least 3 of the metadata fields are set, as not all of them are request.
            self.assertEqual(len(job.output_metadata.keys()) > 3, True)
            job.output_metadata["sampleOrigin"] = "Tissue"
            self.assertEqual(float(job.output_metadata["captureConcentrationNm"]) > 0, True)
            self.assertEqual(
                job.output_metadata["captureConcentrationNm"],
                sum([float(f.metadata["captureConcentrationNm"]) for f in list(FileMetadata.objects.all())])
                / operator_files_count,
            )

            input_json = job.inputs
            self.assertEqual(len(input_json["fgbio_fastq_to_bam_input"]), 2)
            self.assertEqual(len(input_json["fgbio_fastq_to_bam_input"][0]), 2)
            self.assertEqual(len(input_json["fgbio_fastq_to_bam_input"][1]), 2)

    def test_construct_cmo_ch_jobs(self):
        """
        Test that CMO-CH jobs are correctly created
        """
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "05500_HJ.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "05500_HJ.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        files = File.objects.filter(
            filemetadata__metadata__requestId="05500_HJ", filemetadata__metadata__igocomplete=True
        ).all()
        data = list()
        for file in files:
            sample = dict()
            sample["id"] = file.id
            sample["path"] = file.path
            sample["file_name"] = file.file_name
            sample["metadata"] = file.filemetadata_set.first().metadata
            data.append(sample)
        cmo_ch_inputs = construct_sample_inputs(data, "05500_HJ")
        self.assertTrue(len(cmo_ch_inputs) == 18)
        expected_inputs = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "05500_HJ.input.json")))
        cmo_ch_inputs_str = json.dumps(cmo_ch_inputs)
        expected_inputs_str = json.dumps(expected_inputs)
        self.assertTrue(cmo_ch_inputs_str == expected_inputs_str)

    def test_get_cmo_ch_jobs(self):
        """
        Test getting the CMO-CH jobs
        """
        operator_model = Operator.objects.get(id=14)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "05500_HJ.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "05500_HJ.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        jobs = CMOCHNucleoOperator(operator_model, request_id="05500_HJ").get_jobs()
        self.assertTrue((len(jobs) == 18))
        self.assertTrue(jobs[0].name == "CMO-CH Nucleo: 05500_HJ, 1 of 18")
