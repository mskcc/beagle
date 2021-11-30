"""
Tests for Operator Trigger
"""
from mock import patch
from django.test import TestCase
from runner.models import Run
from runner.tasks import check_job_timeouts
from freezegun import freeze_time


class TestRunnerTasks(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "runner.pipeline.json",
        "beagle_etl.operator.json",
        "runner.operator_run.json",
        "runner.run.json",
        "runner.operator_trigger.json",
    ]

    @freeze_time("2018-12-12T22:59:41.044Z")
    @patch('runner.tasks.fail_job')
    def test_timeout_fails_appropriate_jobs(self, fail_job):
        runs = Run.objects.all()
        check_job_timeouts()
        self.assertEqual(fail_job.call_count, 2)
