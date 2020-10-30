import os

from django.test import TestCase
from django.core.management import call_command

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory
from runner.operator.access.v1_0_0.snps_and_indels import AccessLegacySNVOperator


CURDIR = os.path.dirname(os.path.realpath(__file__))
TEST_FIXTURE_DIR = os.path.join(CURDIR, 'fixtures')
FIXTURES = [
    "curated_normal_files.json",
    "curated_normals_file_group.json",
    "curated_normals_file_metadata.json",
    "files.json",
    "files_metadata.json",
    "operator_run.json",
    "ports.json",
    "runs.json",
]

# Todo: how to shorten these to remove folder names like other tests have it?
common_fixtures = [
    'runner/fixtures/runner.pipeline.json',
    'runner/fixtures/runner.run.json',
    'runner/fixtures/runner.operator_run.json',
    'file_system/fixtures/file_system.filegroup.json',
    'file_system/fixtures/file_system.filetype.json',
    'file_system/fixtures/file_system.storage.json',
    'beagle_etl/fixtures/beagle_etl.operator.json',
]
common_fixtures = [os.path.join(ROOT_DIR, f) for f in common_fixtures]


class TestAccessSNVOperator(TestCase):

    fixtures = [os.path.join(TEST_FIXTURE_DIR, f) for f in FIXTURES] + common_fixtures

    def test_access_legacy_snv_operator(self):
        """
        Test that an Access legacy SNV operator instance can be created and used
        """

        # Load fixtures
        for f in self.fixtures:
            test_files_fixture = os.path.join(TEST_FIXTURE_DIR, f)
            call_command('loaddata', test_files_fixture, verbosity=0)

        # Should have:
        # simplex / duplex T bams
        # simplex / duplex N bams
        # simplex / duplex curated N bams
        # so total == 6
        self.assertEqual(len(File.objects.all()), 6)
        self.assertEqual(len(FileMetadata.objects.all()), 6)

        # create access SNV operator
        request_id = "bar"

        # todo: avoid the magic number here:
        operator_model = Operator.objects.get(id=5)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbeaa")
        self.assertEqual(str(operator.model), "AccessLegacySNVOperator")
        self.assertEqual(operator.request_id, "bar")
        self.assertEqual(operator._jobs, [])

        # todo: why should this be 6?
        self.assertEqual(len(operator.files), 6)

        pipeline_slug = "AccessLegacySNVOperator"
        request_id = "access_legacy_snv_test_request"
        access_legacy_snv_model = Operator.objects.get(slug=pipeline_slug)
        operator = AccessLegacySNVOperator(access_legacy_snv_model, request_id=request_id, run_ids=['bc23076e-f477-4578-943c-1fbf6f1fca44'])

        self.assertTrue(isinstance(operator, AccessLegacySNVOperator))
        self.assertTrue(operator.request_id == "access_legacy_snv_test_request")
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
            'genotyping_bams',
            'genotyping_bams_ids',
        ]
        for inputs in input_data:
            for field in required_input_fields:
                self.assertIn(field, inputs)
