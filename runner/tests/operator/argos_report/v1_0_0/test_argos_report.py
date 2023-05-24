"""
Test for constructing argos_report inputs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.argos_report.v1_0_0.argos_report_operator import ArgosReportOperator
from beagle_etl.models import Operator
from notifier.models import JobGroup
from runner.models import Run, Port, Pipeline
from file_system.models import File, FileMetadata, FileGroup, FileType
from file_system.repository.file_repository import FileRepository
from django.conf import settings
from django.core.management import call_command


class TestArgosReportOperator(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "runner.operator_trigger.json",
        "runner.operator_run.json",
        "runner.pipeline.json",
        "beagle_etl.operator.json",
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16.run.json",
        "9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16.samples.json",
        "9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16.files.json",
        "9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16.port.output.json",
        "9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16.port.input.json",
        "BALTO_REQID.file.json",
        "BALTO_REQID.filemetadata.json",
    ]

    def setUp(self):
        os.environ["TMPDIR"] = ""
        self.run_ids = ["9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16"] 
        self.expected_output_directory = "/work/ci/temp/voyager-output/argos/BALTO_REQID/1.1.2/"
        self.expected_project_prefix = "BALTO_REQID"

    def test_get_output_dir(self):
        """
        Test the creation of the output directory

        Since this tests per run_id, this also tests project prefix retrieval (part of output dir path)
        """
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=12)
        argos_report_operator = ArgosReportOperator(
            operator_model,
            pipeline="cf3a6950-30fc-4894-8cdc-3417c1c7bbfc",
            job_group_id=job_group.id,
            run_ids=self.run_ids,
        )
        pipeline = Pipeline.objects.get(id=argos_report_operator.get_pipeline_id())
        for run_id in self.run_ids:
            run = Run.objects.get(id=run_id)
            project_prefix = run.tags["project_prefix"]
            output_directory = argos_report_operator.gen_output_dir(pipeline, project_prefix)
            expected_output_directory_with_timestamp = os.path.join(
                self.expected_output_directory, job_group.created_date.strftime("%Y%m%d_%H_%M_%f"), "report"
            )
            self.assertEqual(output_directory, expected_output_directory_with_timestamp)

    def test_gen_inputs(self):
        expected_inputs = json.load(open("runner/tests/operator/argos_report/v1_0_0/test_argos_report_expected_inputs.json", "rb"))
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=12)
        argos_report_operator = ArgosReportOperator(
            operator_model,
            pipeline="cf3a6950-30fc-4894-8cdc-3417c1c7bbfc",
            job_group_id=job_group.id,
            run_ids=self.run_ids,
        )
        run = Run.objects.get(id=self.run_ids[0])
        my_generated_inputs = argos_report_operator.gen_inputs(run)        
        expected = json.dumps(sorted(expected_inputs, key=lambda d: d["sample_id"]))
        actual = json.dumps(sorted(my_generated_inputs, key=lambda d: d["sample_id"]))
        self.maxDiff = None
        self.assertEqual(expected, actual)