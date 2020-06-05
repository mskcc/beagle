"""
Tests for Operator Trigger
"""
import os
import uuid
from mock import patch, call
from django.test import TestCase
from runner.models import OperatorRun, RunStatus, TriggerRunType, OperatorTrigger, Run
from runner.tasks import process_triggers, complete_job, fail_job, create_jobs_from_operator
from beagle_etl.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.serializers import APIRunCreateSerializer


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
    @patch('runner.tasks.create_run_task')
    @patch('notifier.tasks.send_notification')
    @patch('runner.operator.argos_operator.ArgosOperator.get_jobs')
    @patch('runner.operator.argos_operator.ArgosOperator.get_pipeline_id')
    def test_create_jobs_from_operator_pipeline_deleted(self, get_pipeline_id, get_jobs, send_notification, create_run_task):
        argos_jobs = []
        argos_jobs.append((APIRunCreateSerializer(
                data={'app': 'cb5d793b-e650-4b7d-bfcd-882858e29cc5', 'inputs': None, 'name': None,}), None))
        get_jobs.return_value = argos_jobs
        get_pipeline_id.return_value = None
        create_run_task.return_value = None
        send_notification.return_value = None
        Run.objects.all().delete()

        operator = OperatorFactory.get_by_model(Operator.objects.get(id=1), request_id="bar")
        create_jobs_from_operator(operator,None)
        self.assertEqual(len(Run.objects.all()),1)
        self.assertEqual(Run.objects.first().status, RunStatus.FAILED)


    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_creates_next_operator_run_when_90percent_runs_completed(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            complete_job(run_id, "done")

        process_triggers()
        operator_run.refresh_from_db()
        trigger = operator_run.operator.from_triggers.first()

        create_jobs_from_chaining.delay.assert_called_once_with(trigger.to_operator.pk,
                                                                trigger.from_operator.pk,
                                                                run_ids, job_group_id=None)
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)


    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_does_not_create_next_operator_run_when_too_few_runs_completed(self,
                                                                                            create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        complete_job(run_ids[0], "done")

        process_triggers()

        create_jobs_from_chaining.delay.assert_not_called()

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_fails_operator_run_when_all_runs_are_complete_and_no_threshold_is_met(self, create_jobs_from_chaining):
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            fail_job(run_id, "done")

        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.FAILED)

    @patch('runner.tasks.create_jobs_from_chaining')
    def test_operator_trigger_executes_runs_individually(self, create_jobs_from_chaining):
        for op_run in OperatorRun.objects.prefetch_related("runs").all():
            for t in op_run.operator.from_triggers.all():
                if t.run_type == TriggerRunType.INDIVIDUAL:
                    operator_run = op_run
                    trigger = t
                    break

        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            complete_job(run_id, "done")

        calls = [
            call(trigger.to_operator.pk,
                 trigger.from_operator.pk,
                 [run_ids[0]], job_group_id=None
                 ),
            call(trigger.to_operator.pk,
                 trigger.from_operator.pk,
                 [run_ids[1]], job_group_id=None
                 ),
            call(trigger.to_operator.pk,
                 trigger.from_operator.pk,
                 [run_ids[2]], job_group_id=None
                 )
        ]

        create_jobs_from_chaining.delay.assert_has_calls(calls, any_order=True)
        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)

