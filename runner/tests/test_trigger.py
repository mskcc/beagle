"""
Tests for Operator Trigger
"""
import os
import uuid
from mock import patch, call
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator
from runner.models import OperatorRun, RunStatus, TriggerRunType
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
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").filter(trigger__run_type=TriggerRunType.AGGREGATE).first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            complete_job(run_id, "done")

        process_triggers()
        operator_run.refresh_from_db()

        create_jobs_from_chaining.delay.assert_called_once_with(operator_run.trigger.to_operator.pk,
                                     operator_run.trigger.from_operator.pk,
                                     run_ids)
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)


    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_does_not_create_next_operator_run_when_too_few_runs_completed(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").filter(trigger__run_type=TriggerRunType.AGGREGATE).first()
        run_ids = [run.id for run in operator_run.runs.all()]
        complete_job(run_ids[0], "done")

        process_triggers()

        create_jobs_from_chaining.delay.assert_not_called()

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_fails_operator_run_when_all_runs_are_complete_and_no_threshold_is_met(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").filter(trigger__run_type=TriggerRunType.AGGREGATE).first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            fail_job(run_id, "done")

        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.FAILED)

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_executes_runs_individually(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs", "trigger").filter(trigger__run_type=TriggerRunType.INDIVIDUAL).first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            complete_job(run_id, "done")


        calls = [
            call(operator_run.trigger.to_operator.pk,
                 operator_run.trigger.from_operator.pk,
                 [run_ids[0]]
                 ),
            call(operator_run.trigger.to_operator.pk,
                 operator_run.trigger.from_operator.pk,
                 [run_ids[1]]
                 ),
            call(operator_run.trigger.to_operator.pk,
                 operator_run.trigger.from_operator.pk,
                 [run_ids[2]]
                 )
        ]

        create_jobs_from_chaining.delay.assert_has_calls(calls, any_order=True)
        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)

