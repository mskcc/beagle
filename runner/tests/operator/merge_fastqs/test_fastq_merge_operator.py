import os

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory
from runner.operator.access.v1_0_0.merge_fastqs import AccessLegacyFastqMergeOperator, construct_inputs


FIXTURES = [
    #"fixtures/tests/merge_fastqs/curated_normal_files.json",
    #"fixtures/tests/access_fastq_merge/curated_normals_file_metadata.json",
    "fixtures/tests/merge_fastqs/10151_F_13.file.json",
    "fixtures/tests/merge_fastqs/10151_F_13.filemetadata.json",
    #"fixtures/tests/access_fastq_merge/files_metadata.json",
    #"fixtures/tests/access_fastq_merge/operator_run.json",
    #"fixtures/tests/access_fastq_merge/ports.json",
    #"fixtures/tests/access_fastq_merge/runs.json",
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


class TestAccessFastqMergeOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_access_legacy_fastq_merge_operator(self):
        """
        Test that an Access legacy FastqMerge operator instance can be created and validated
        """
        # Test should have all Files / FileMetadata from fixtures
        operator_files_count = 4
        self.assertEqual(len(File.objects.all()), operator_files_count)
        self.assertEqual(len(FileMetadata.objects.all()), operator_files_count)

        # create access FastqMerge operator
        request_id = "10151_F"

        # todo: avoid the magic number here:
        operator_model = Operator.objects.get(id=8)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cdffffff")
        self.assertEqual(str(operator.model), "AccessLegacyFastqMergeOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job[0].is_valid(), True)
            input_json = job[0].initial_data['inputs']
            self.assertEqual(len(input_json["fastq1"]), 2)
            self.assertEqual(len(input_json["fastq2"]), 2)

