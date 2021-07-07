import os

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory


FIXTURES = [
    "runner/tests/operator/access/v2_0_0/qc/files_fixture.json",
    "runner/tests/operator/access/v2_0_0/qc/files_metadata_fixture.json",
    "runner/tests/operator/access/v2_0_0/qc/ports_fixture.json",
]

COMMON_FIXTURES = [
    'runner/fixtures/runner.pipeline.json',
    'runner/fixtures/runner.run.json',
    'runner/fixtures/runner.operator_run.json',
    'file_system/fixtures/file_system.filegroup.json',
    'file_system/fixtures/file_system.filetype.json',
    'file_system/fixtures/file_system.storage.json',
    'beagle_etl/fixtures/beagle_etl.operator.json',
]


class TestAccessQCOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_access_nucleo_operator(self):
        """
        Test that an ACCESS QC operator instance can be created and validated
        """
        operator_files_count = 5
        self.assertEqual(len(File.objects.all()), operator_files_count)
        self.assertEqual(len(FileMetadata.objects.all()), operator_files_count)

        request_id = "05500_FH"

        operator_model = Operator.objects.get(id=11)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "05419097-a2b8-4d57-a8ab-c4c4cddcbabc")
        self.assertEqual(str(operator.model), "AccessQCOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job[0].is_valid(), True)
            input_json = job[0].initial_data["inputs"]
            self.assertEqual(len(input_json["collapsed_bam"]), 1)
            self.assertEqual(len(input_json["duplex_bam"]), 1)
            self.assertEqual(len(input_json["group_reads_by_umi_bam"]), 1)
            self.assertEqual(len(input_json["simplex_bam"]), 1)
            self.assertEqual(len(input_json["uncollapsed_bam_base_recal"]), 1)
            self.assertEqual(len(input_json["sample_group"]), 1)
            self.assertEqual(len(input_json["sample_name"]), 1)
            self.assertEqual(len(input_json["sample_sex"]), 1)
            self.assertIsNotNone(input_json["samples-json"])