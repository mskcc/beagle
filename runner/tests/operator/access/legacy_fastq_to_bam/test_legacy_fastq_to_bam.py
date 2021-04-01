import os

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory


FIXTURES = [
    "fixtures/tests/access_fastq_to_bam/10151_F.file.json",
    "fixtures/tests/access_fastq_to_bam/10151_F.filemetadata.json",
    "fixtures/tests/access_fastq_to_bam/10151_F.port.json",
    "fixtures/tests/access_fastq_to_bam/10151_F.run.json",
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


class TestAccessLegacyOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_access_legacy_operator(self):
        """
        Test that an Access legacy operator instance can be created and validated
        """
        operator_files_count = 2
        self.assertEqual(len(File.objects.all()), operator_files_count)
        self.assertEqual(len(FileMetadata.objects.all()), operator_files_count)

        request_id = "access_merge_fastq_test_request"

        operator_model = Operator.objects.get(id=3)
        operator = OperatorFactory.get_by_model(
            operator_model,
            request_id=request_id,
            run_ids=['bc23076e-f477-4578-943c-1fbf6f1fca44']
        )
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbeac")
        self.assertEqual(str(operator.model), "AccessOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job[0].is_valid(), True)
            input_json = job[0].initial_data['inputs']
            self.assertEqual(len(input_json["fastq1"]), 1)
            self.assertEqual(len(input_json["fastq2"]), 1)

