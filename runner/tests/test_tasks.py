"""
Tests for Operator Trigger
"""
import os
from mock import patch
from django.conf import settings
from django.test import TestCase
from runner.models import Run
from runner.tasks import check_job_timeouts, check_operator_run_alerts
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
        "file_system.sample.json",
        "notifier.json",
        "operator_run_manual_restart",
        "runner.operator_trigger.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.files.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.port.input.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.port.output.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.run.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.samples.json",
    ]

    @freeze_time("2018-12-12T22:59:41.044Z")
    @patch("runner.tasks.fail_job")
    def test_timeout_fails_appropriate_jobs(self, fail_job):
        runs = Run.objects.all()
        check_job_timeouts()
        self.assertEqual(fail_job.call_count, 2)

    def test_operator_run_check(self):
        check_operator_run_alerts()
        file_written = os.path.exists(settings.MANUAL_RESTART_REPORT_PATH)
        self.assertTrue(file_written)
