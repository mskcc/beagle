import os

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.operator.access.v1_0_0.structural_variants import AccessLegacySVOperator


FIXTURES = [
    "fixtures/tests/access_snv/curated_normal_files.json",
    "fixtures/tests/access_snv/curated_normals_file_metadata.json",
    "fixtures/tests/access_snv/files.json",
    "fixtures/tests/access_snv/files_metadata.json",
    "fixtures/tests/access_snv/operator_run.json",
    "fixtures/tests/access_snv/ports.json",
    "fixtures/tests/access_snv/runs.json",
    "fixtures/tests/access_snv/sv_bams/files.json",
    "fixtures/tests/access_snv/sv_bams/files_metadata.json",
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


class TestAccessSVOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_access_legacy_sv_operator(self):
        """
        Test that an Access legacy SV operator instance can be created and validated
        """
        # create access SV operator
        request_id = "access_legacy_test_request"

        # todo: avoid the magic number here:
        operator_model = Operator.objects.get(id=6)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbead")
        self.assertEqual(str(operator.model), "AccessLegacySVOperator")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        pipeline_slug = "AccessLegacySVOperator"
        access_legacy_sv_model = Operator.objects.get(slug=pipeline_slug)
        operator = AccessLegacySVOperator(access_legacy_sv_model, request_id=request_id, run_ids=['bc23076e-f477-4578-943c-1fbf6f1fca44'])

        self.assertTrue(isinstance(operator, AccessLegacySVOperator))
        self.assertTrue(operator.request_id == request_id)
        self.assertTrue(operator._jobs == [])
        self.assertEqual(operator.run_ids, ['bc23076e-f477-4578-943c-1fbf6f1fca44'])
        self.assertEqual(operator.get_pipeline_id(), "65419097-a2b8-4d57-a8ab-c4c4cddcbead")

        # Create and validate the input data
        input_data = operator.get_sample_inputs()

        required_input_fields = [
            'sv_sample_id',
            'sv_tumor_bams',
        ]
        self.assertEqual(len(input_data), 1)
        for inputs in input_data:
            for field in required_input_fields:
                self.assertIn(field, inputs)
                self.assertEqual(len(inputs[field]), 1)
            self.assertIn('sv_normal_bam', inputs)
