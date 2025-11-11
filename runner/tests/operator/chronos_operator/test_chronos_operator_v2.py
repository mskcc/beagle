"""
Test for constructing argos_report inputs
"""
import os
import json

from django.test import TestCase
from runner.operator.chronos_operator_v2.chronos_operator import ChronosOperatorV2
from beagle_etl.models import Operator
from notifier.models import JobGroup
from runner.models import Run, Port, Pipeline
from file_system.models import File, FileMetadata, FileGroup, FileType

class TestChronosOperatorV2(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "runner.pipeline.json",
        "beagle_etl.operator.json",
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "file_system.chronos.files.json",
    ]

    def setUp(self):
        os.environ["TMPDIR"] = ""
        self.request_id = "16083_B"
        self.primary_id = "16083_B_31"
        self.run_ids = ["9fc2d168-efb1-11ed-b8bf-ac1f6bb4ad16"]
        self.expected_output_directory = "/work/ci/temp/voyager-output/argos/BALTO_REQID/1.1.2/"
        self.expected_project_prefix = "BALTO_REQID"

    def test_gen_inputs(self):
        chronos_operator = self.load_operator_request()
        jobs = chronos_operator.get_jobs()
        self.assertEqual(len(jobs), 1)

    def test_gen_inputs_pairs(self):
        chronos_operator = self.load_operator_pairs()
        jobs = chronos_operator.get_jobs()
        self.assertEqual(len(jobs), 1)

    def load_operator_request(self):
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=34)
        chronos_operator = ChronosOperatorV2(
            operator_model,
            pipeline="ec65d7ec-4638-11f0-aafb-f68a3351235e",
            job_group_id=job_group.id,
            request_id=self.request_id,
            file_group="40ad84eb-0694-446b-beac-59e35e154f3c"
        )
        return chronos_operator

    def load_operator_pairs(self):
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=34)
        chronos_operator = ChronosOperatorV2(
            operator_model,
            pipeline="ec65d7ec-4638-11f0-aafb-f68a3351235e",
            job_group_id=job_group.id,
            pairing={"pairs":[{"tumor": self.primary_id, "normal": None}]},
            file_group="40ad84eb-0694-446b-beac-59e35e154f3c"
        )
        return chronos_operator
