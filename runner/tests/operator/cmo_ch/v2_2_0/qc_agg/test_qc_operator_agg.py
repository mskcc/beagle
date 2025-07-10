import os

from django.test import TestCase

from beagle import settings
from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory


FIXTURES = [
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/faffb78c-f4c8-11ed-a5fd-ac1f6bb4ad16.port.input.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/faffb78c-f4c8-11ed-a5fd-ac1f6bb4ad16.port.output.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/faffb78c-f4c8-11ed-a5fd-ac1f6bb4ad16.run.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/faffb78c-f4c8-11ed-a5fd-ac1f6bb4ad16.files.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/faffb78c-f4c8-11ed-a5fd-ac1f6bb4ad16.samples.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/fb00b43e-f4c8-11ed-a5fd-ac1f6bb4ad16.port.input.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/fb00b43e-f4c8-11ed-a5fd-ac1f6bb4ad16.port.output.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/fb00b43e-f4c8-11ed-a5fd-ac1f6bb4ad16.run.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/fb00b43e-f4c8-11ed-a5fd-ac1f6bb4ad16.files.json",
    "runner/tests/operator/cmo_ch/v2_2_0/qc_agg/fb00b43e-f4c8-11ed-a5fd-ac1f6bb4ad16.samples.json",
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

    def test_cmo_qc_agg_operator(self):
        """
        Test that an CMO CH QC AGGREGATE operator instance can be created and validated
        """
        # self.assertEqual(len(File.objects.all()), 35)
        # self.assertEqual(len(FileMetadata.objects.all()), 35)

        # This operator needs to write a temp file, so need to override this env var
        settings.BEAGLE_SHARED_TMPDIR = "/tmp"
        request_id = "13843_C"
        operator_model = Operator.objects.get(id=31)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "8c256be3-21b7-4640-9d54-bb5bba42db58")
        self.assertEqual(str(operator.model), "CMOCHNucleoOperatorQcAgg_2_2_0")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])
        jobs = operator.get_jobs()

        self.assertEqual(len(jobs) > 0, True)
        for job in jobs:
            self.assertEqual(job.is_valid(), True)
            input_json = job.inputs
            self.assertEqual(len(input_json["athena_coverage_report_dir"]), 0)
            self.assertEqual(len(input_json["collapsed_bam_duplex_metrics_dir"]), 2)
            self.assertEqual(len(input_json["collapsed_bam_stats_dir"]), 2)
            self.assertEqual(len(input_json["collapsed_extraction_files"]), 2)
            self.assertEqual(len(input_json["duplex_bam_sequence_qc_dir"]), 2)
            self.assertEqual(len(input_json["duplex_bam_stats_dir"]), 2)
            self.assertEqual(len(input_json["duplex_extraction_files"]), 2)
            self.assertEqual(len(input_json["gatk_mean_quality_by_cycle_recal_dir"]), 2)
            self.assertEqual(len(input_json["simplex_bam_stats_dir"]), 2)
            self.assertEqual(len(input_json["uncollapsed_bam_stats_dir"]), 2)
            self.assertEqual(len(input_json["biometrics_extract_files_dir"]), 2)
            self.assertIsNotNone(input_json["samples-json"])
            self.assertIsNotNone(input_json["config"])
