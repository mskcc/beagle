"""
Tests for Operator Trigger
"""
import os
import uuid
from mock import patch
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator
from runner.models import OperatorRun, RunStatus
from django.conf import settings
from django.core.management import call_command
from file_system.models import File, FileMetadata, FileGroup, FileType
from pprint import pprint
from runner.tasks import process_triggers, complete_job, fail_job

class TestOperatorTriggers(TestCase):
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

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_creates_next_operator_run_when_90percent_runs_completed(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            complete_job(run_id, "done")

        process_triggers()

        create_jobs_from_chaining.delay.assert_called_once_with(operator_run.trigger.to_operator.pk,
                                     operator_run.trigger.from_operator.pk,
                                     run_ids)


    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_does_not_create_next_operator_run_when_too_few_runs_completed(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        complete_job(run_ids[0], "done")

        process_triggers()

        create_jobs_from_chaining.delay.assert_not_called()

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_fails_operator_run_when_all_runs_are_complete_and_no_threshold_is_met(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            fail_job(run_id, "done")

        operator_run.refresh_from_db()
        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.FAILED)
