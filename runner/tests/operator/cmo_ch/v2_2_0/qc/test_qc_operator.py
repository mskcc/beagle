import os

from django.test import TestCase

from beagle import settings
from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory


FIXTURES = [
    "runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.files.json",
    "runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.input.json",
    "runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.output.json",
    "runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.run.json",
    "runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.samples.json",
]

COMMON_FIXTURES = [
    "runner/fixtures/runner.pipeline.json",
    "runner/fixtures/runner.operator_run.json",
    "file_system/fixtures/file_system.filegroup.json",
    "file_system/fixtures/file_system.filetype.json",
    "file_system/fixtures/file_system.storage.json",
    "beagle_etl/fixtures/beagle_etl.operator.json",
]


class TestNucleoQCOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]

    def test_cmo_qc_operator(self):
        """
        Test that an CMO CH QC operator instance can be created and validated
        """
        self.assertEqual(len(File.objects.all()), 35)
        self.assertEqual(len(FileMetadata.objects.all()), 35)

        # This operator needs to write a temp file, so need to override this env var
        settings.BEAGLE_SHARED_TMPDIR = "/tmp"
        request_id = "12405_C"

        operator_model = Operator.objects.get(id=27)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "0a7e5820-ea7f-11ed-b755-ac1f6bb4ad26")
        self.assertEqual(str(operator.model), "CMOCHNucleoOperatorQC_2_2_0")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])

        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job.is_valid(), True)
            input_json = job.inputs
            self.assertEqual(len(input_json["collapsed_bam"]), 1)
            self.assertEqual(len(input_json["duplex_bam"]), 1)
            self.assertEqual(len(input_json["group_reads_by_umi_bam"]), 1)
            self.assertEqual(len(input_json["simplex_bam"]), 1)
            self.assertEqual(len(input_json["uncollapsed_bam_base_recal"]), 1)
            self.assertEqual(len(input_json["sample_group"]), 1)
            self.assertEqual(len(input_json["sample_name"]), 1)
            self.assertEqual(len(input_json["sample_sex"]), 1)
            self.assertIsNotNone(input_json["samples-json"])
