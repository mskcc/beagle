"""
Test for constructing argos_report inputs
"""

import os
import tempfile
import json
from pathlib import Path
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.argos_report.v1_3_0.argos_report_operator import ArgosReportOperator
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
        self.expected_output_directory = "/work/ci/temp/voyager-output/argos/BALTO_REQID/1.8.0/"
        self.expected_project_prefix = "BALTO_REQID"

    def test_get_output_dir(self):
        """
        Test the creation of the output directory

        Since this tests per run_id, this also tests project prefix retrieval (part of output dir path)
        """
        argos_report_operator = self.load_operator()
        job_group = JobGroup.objects.get(id=argos_report_operator.job_group_id)
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
        expected_inputs = json.load(
            open("runner/tests/operator/argos_report/v1_3_0/test_argos_report_expected_inputs.json", "rb")
        )
        argos_report_operator = self.load_operator()
        tmpdir = self._create_tmp_annotations_dir()
        files = os.listdir(tmpdir.name)
        argos_report_operator.annotations_path = "iris://" + tmpdir.name
        run = Run.objects.get(id=self.run_ids[0])
        my_generated_inputs = argos_report_operator.gen_inputs(run)
        my_generated_inputs["oncokb_file"]["location"] = my_generated_inputs["oncokb_file"]["location"].replace(
            tmpdir.name, "/tmp/oncokb/dir"
        )
        expected = json.dumps(expected_inputs)
        actual = json.dumps(my_generated_inputs)
        self.maxDiff = None
        self.assertEqual(expected, actual)

    def load_operator(self):
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=12)
        argos_report_operator = ArgosReportOperator(
            operator_model,
            pipeline="cf3a6950-30fc-4894-8cdc-3417c1c7bbfc",
            job_group_id=job_group.id,
            run_ids=self.run_ids,
        )
        return argos_report_operator

    def test_create_file_obj(self):
        op = self.load_operator()
        file_exists = File.objects.get(id="7e9c55b1-d8b5-4767-80a6-dfa382918ffb")
        file_group = file_exists.file_group
        file_type = file_exists.file_type
        file_create_false = op._create_file_obj(path=file_exists.path, file_group=file_group, file_type=file_type)
        file_not_exists = "/tmp/nonexistent_fake_file.txt"
        file_create_true = op._create_file_obj(path=file_not_exists, file_group=file_group, file_type=file_type)
        self.assertFalse(file_create_false)
        self.assertTrue(file_create_true)

    def _create_tmp_annotations_dir(self):
        tmpdir = tempfile.TemporaryDirectory()
        Path(os.path.join(tmpdir.name, "oncokb.db.v230119.rds")).touch()
        Path(os.path.join(tmpdir.name, "oncokb.db.v230127.rds")).touch()
        Path(os.path.join(tmpdir.name, "oncokb.db.v230427.rds")).touch()
        return tmpdir
