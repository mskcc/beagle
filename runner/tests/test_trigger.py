"""
Tests for Operator Trigger
"""
from mock import patch, call
from django.test import TestCase
from beagle_etl.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.run.objects.run_creator_object import RunCreator
from runner.models import OperatorRun, RunStatus, TriggerRunType, Run
from runner.tasks import process_triggers, complete_job, fail_job, create_jobs_from_operator


class TestOperatorTriggers(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "runner.pipeline.json",
        "beagle_etl.operator.json",
        "runner.operator_run.json",
        "runner.run.json",
        "file_system.sample.json",
        "runner.operator_trigger.json",
    ]

    @patch("runner.models.Run.set_for_restart")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.tasks.create_run_task")
    @patch("notifier.tasks.send_notification.delay")
    @patch("runner.operator.argos_operator.v1_0_0.ArgosOperator.get_jobs")
    @patch("runner.operator.argos_operator.v1_0_0.ArgosOperator.get_pipeline_id")
    @patch("runner.tasks._job_finished_notify")
    def test_create_jobs_from_operator_pipeline_deleted(
        self,
        job_finished_notify,
        get_pipeline_id,
        get_jobs,
        send_notification,
        create_run_task,
        memcache_task_lock,
        set_for_restart,
    ):
        argos_jobs = list()
        argos_jobs.append(RunCreator(app="cb5d793b-e650-4b7d-bfcd-882858e29cc5", inputs=None, name=None, tags={}))
        job_finished_notify.return_value = None
        set_for_restart.return_value = None
        get_jobs.return_value = argos_jobs
        get_pipeline_id.return_value = None
        create_run_task.return_value = None
        send_notification.return_value = None
        memcache_task_lock.return_value = True
        Run.objects.all().delete()

        operator = OperatorFactory.get_by_model(Operator.objects.get(id=1), request_id="bar")
        create_jobs_from_operator(operator, None)
        self.assertEqual(len(Run.objects.all()), 1)
        self.assertEqual(RunStatus(Run.objects.first().status), RunStatus.FAILED)

    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.tasks.create_jobs_from_chaining")
    @patch("runner.tasks._job_finished_notify")
    def test_operator_trigger_creates_next_operator_run_when_90percent_runs_completed(
        self, job_finished_notify, create_jobs_from_chaining, memcache_task_lock, send_notification
    ):
        job_finished_notify.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = list(operator_run.runs.order_by("id").values_list("id", flat=True))
        for run_id in run_ids:
            complete_job(run_id, "done")

        process_triggers()
        operator_run.refresh_from_db()
        trigger = operator_run.operator.from_triggers.first()

        create_jobs_from_chaining.delay.assert_called_once_with(
            trigger.to_operator.pk,
            trigger.from_operator.pk,
            run_ids,
            job_group_id=None,
            job_group_notifier_id=None,
            parent=str(operator_run.id),
        )
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)

    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.tasks.create_jobs_from_chaining")
    @patch("runner.tasks._job_finished_notify")
    def test_operator_trigger_does_not_create_next_operator_run_when_too_few_runs_completed(
        self, job_finished_notify, create_jobs_from_chaining, memcache_task_lock, send_notification
    ):
        job_finished_notify.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = list(operator_run.runs.order_by("id").values_list("id", flat=True))
        complete_job(run_ids.pop(), "done")

        process_triggers()

        create_jobs_from_chaining.delay.assert_not_called()

    @patch("runner.models.Run.set_for_restart")
    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.tasks._job_finished_notify")
    def test_operator_trigger_fails_operator_run_when_all_runs_are_complete_and_no_threshold_is_met(
        self, job_finished_notify, memcache_task_lock, send_notification, set_for_restart
    ):
        job_finished_notify.return_value = None
        set_for_restart.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        operator_run = OperatorRun.objects.prefetch_related("runs").first()
        run_ids = [run.id for run in operator_run.runs.all()]
        for run_id in run_ids:
            message = dict(details="done")
            fail_job(run_id, message)

        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.FAILED)

    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.tasks.create_jobs_from_chaining")
    @patch("runner.tasks._job_finished_notify")
    def test_operator_trigger_executes_runs_individually(
        self, job_finished_notify, create_jobs_from_chaining, memcache_task_lock, send_notification
    ):
        job_finished_notify.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
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
            call(
                trigger.to_operator.pk,
                trigger.from_operator.pk,
                [run_ids[0]],
                job_group_id=None,
                parent=str(operator_run.id),
            ),
            call(
                trigger.to_operator.pk,
                trigger.from_operator.pk,
                [run_ids[1]],
                job_group_id=None,
                parent=str(operator_run.id),
            ),
            call(
                trigger.to_operator.pk,
                trigger.from_operator.pk,
                [run_ids[2]],
                job_group_id=None,
                parent=str(operator_run.id),
            ),
        ]

        create_jobs_from_chaining.delay.assert_has_calls(calls, any_order=True)
        process_triggers()
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.status, RunStatus.COMPLETED)
