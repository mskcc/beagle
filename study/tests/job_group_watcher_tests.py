from mock import patch
from rest_framework.test import APITestCase
from study.tasks import check_job_group_watcher
from beagle_etl.models import Operator as EtlOperator
from operator_manager.models import Operator, OperatorRun, OperatorStatus, OperatorVersion
from notifier.models import JobGroup
from runner.models import RunStatus
from study.models import Study, JobGroupWatcher, JobGroupWatcherConfig, JobGroupWatcherStatus


class TestStudy(APITestCase):
    @staticmethod
    def _create_operator(etl_operator):
        # JobGroupWatcherConfig still references beagle_etl.Operator; operator_manager.Operator shares its ids
        return Operator.objects.create(
            id=etl_operator.id,
            name=etl_operator.slug,
            type=OperatorVersion.V1,
            status=OperatorStatus.READY,
            class_name=etl_operator.class_name,
            version=etl_operator.version,
            active=True,
        )

    def setUp(self):
        self.study = Study.objects.create(study_id="test_study_id")
        self.job_group = JobGroup.objects.create()
        self.etl_operator_1 = EtlOperator.objects.create(
            slug="OperatorClass1", class_name="operator_1.OperatorClass1", version="1.0.0", active=True, recipes=[]
        )
        self.operator_1 = self._create_operator(self.etl_operator_1)
        self.etl_operator_2 = EtlOperator.objects.create(
            slug="OperatorClass2", class_name="operator_2.OperatorClass2", version="1.0.0", active=True, recipes=[]
        )
        self.operator_2 = self._create_operator(self.etl_operator_2)
        self.etl_operator_3 = EtlOperator.objects.create(
            slug="OperatorClass3", class_name="operator_3.OperatorClass3", version="1.0.0", active=True, recipes=[]
        )
        self.operator_3 = self._create_operator(self.etl_operator_3)
        self.operator_run_1 = OperatorRun.objects.create(
            status=RunStatus.RUNNING,
            operator=self.operator_1,
            num_total_runs=2,
            num_completed_runs=1,
            job_group=self.job_group,
        )
        self.operator_run_2 = OperatorRun.objects.create(
            status=RunStatus.RUNNING,
            operator=self.operator_2,
            num_total_runs=2,
            num_completed_runs=1,
            job_group=self.job_group,
        )
        self.job_group_watcher_config = JobGroupWatcherConfig.objects.create(
            name="TestWatcher",
        )
        self.job_group_watcher_config.operators.add(self.etl_operator_1)
        self.job_group_watcher_config.operators.add(self.etl_operator_2)
        self.job_group_watcher_config.post_processors.add(self.etl_operator_3)
        self.job_group_watcher = JobGroupWatcher.objects.create(
            study=self.study,
            job_group=self.job_group,
            config=self.job_group_watcher_config,
            status=JobGroupWatcherStatus.WAITING,
        )

    @patch("study.tasks.kick_off_postprocessing")
    def test_job_group_watcher_operators_still_running(self, kick_off_postprocessing):
        # Check job group watcher when both OperatorRuns are Running
        kick_off_postprocessing.return_value = True
        check_job_group_watcher()
        self.job_group_watcher.refresh_from_db()
        self.assertEqual(JobGroupWatcherStatus(self.job_group_watcher.status), JobGroupWatcherStatus.WAITING)

    @patch("study.tasks.kick_off_postprocessing")
    def test_job_group_watcher_operators_both_completed(self, kick_off_postprocessing):
        # Check job group watcher when both OperatorRuns are completed
        kick_off_postprocessing.return_value = True
        self.operator_run_1.increment_completed_run()
        self.operator_run_1.complete()
        self.operator_run_1.refresh_from_db()
        self.operator_run_2.increment_completed_run()
        self.operator_run_2.complete()
        self.operator_run_2.refresh_from_db()
        check_job_group_watcher()
        self.job_group_watcher.refresh_from_db()
        self.assertEqual(JobGroupWatcherStatus(self.job_group_watcher.status), JobGroupWatcherStatus.COMPLETED)
        self.assertTrue(kick_off_postprocessing.called)

    @patch("study.tasks.kick_off_postprocessing")
    def test_job_group_watcher_operators_one_failed(self, kick_off_postprocessing):
        # Check job group watcher when one OperatorRun fails
        kick_off_postprocessing.return_value = True
        self.operator_run_1.increment_completed_run()
        self.operator_run_1.complete()
        self.operator_run_2.increment_failed_run()
        self.operator_run_2.fail()
        self.operator_run_1.refresh_from_db()
        self.operator_run_2.refresh_from_db()
        check_job_group_watcher()
        self.job_group_watcher.refresh_from_db()
        self.assertEqual(JobGroupWatcherStatus(self.job_group_watcher.status), JobGroupWatcherStatus.COMPLETED)
        self.assertTrue(kick_off_postprocessing.called)
