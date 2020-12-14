import os

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory
from runner.operator.access.v1_0_0.snps_and_indels import AccessLegacySNVOperator


FIXTURES = [
    "fixtures/tests/access_snv/curated_normal_files.json",
    "fixtures/tests/access_snv/curated_normals_file_metadata.json",
    "fixtures/tests/access_snv/files.json",
    "fixtures/tests/access_snv/files_metadata.json",
    "fixtures/tests/access_snv/operator_run.json",
    "fixtures/tests/access_snv/ports.json",
    "fixtures/tests/access_snv/runs.json",
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


class TestAccessSNVOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_access_legacy_snv_operator(self):
        """
        Test that an Access legacy SNV operator instance can be created and validated
        """
        # Test should have all Files / FileMetadata from fixtures
        operator_files_count = 10
        self.assertEqual(len(File.objects.all()), operator_files_count)
        self.assertEqual(len(FileMetadata.objects.all()), operator_files_count)

        # create access SNV operator
        request_id = "access_legacy_test_request"

        # todo: avoid the magic number here:
        operator_model = Operator.objects.get(id=5)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbeaa")
        self.assertEqual(str(operator.model), "AccessLegacySNVOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        # todo: why should this be 6?
        self.assertEqual(len(operator.files), operator_files_count)

        pipeline_slug = "AccessLegacySNVOperator"
        access_legacy_snv_model = Operator.objects.get(slug=pipeline_slug)
        operator = AccessLegacySNVOperator(access_legacy_snv_model, request_id=request_id, run_ids=['bc23076e-f477-4578-943c-1fbf6f1fca44'])

        self.assertTrue(isinstance(operator, AccessLegacySNVOperator))
        self.assertTrue(operator.request_id == request_id)
        self.assertTrue(operator._jobs == [])
        self.assertEqual(operator.run_ids, ['bc23076e-f477-4578-943c-1fbf6f1fca44'])
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbeaa")

        # Create and validate the input data
        input_data = operator.get_sample_inputs()

        required_input_fields = [
            'tumor_bams',
            'normal_bams',
            'tumor_sample_names',
            'normal_sample_names',
            'matched_normal_ids',
        ]
        required_input_fields_length_3 = [
            'genotyping_bams',
            'genotyping_bams_ids',
        ]
        for inputs in input_data:
            for field in required_input_fields:
                self.assertIn(field, inputs)
                self.assertEqual(len(inputs[field]), 1)
            for field in required_input_fields_length_3:
                self.assertIn(field, inputs)
                self.assertEqual(len(inputs[field]), 5)
