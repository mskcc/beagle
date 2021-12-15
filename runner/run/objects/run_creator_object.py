import logging
import datetime
from notifier.models import JobGroup, JobGroupNotifier
from runner.models import Pipeline, Run, RunStatus, OperatorRun


class RunCreator(object):
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        app,
        inputs,
        name,
        tags,
        output_directory=None,
        output_metadata={},
        operator_run_id=None,
        job_group_id=None,
        job_group_notifier_id=None,
        notify_for_outputs=[],
        resume=None,
    ):
        self.app = app
        self.inputs = inputs
        self.name = name
        self.tags = tags
        self.output_directory = output_directory
        self.output_metadata = output_metadata
        self.operator_run_id = operator_run_id
        self.job_group_id = job_group_id
        self.job_group_notifier_id = job_group_notifier_id
        self.notify_for_outputs = notify_for_outputs
        self.resume = resume

    def create(self):
        try:
            pipeline = Pipeline.objects.get(id=self.app)
        except Pipeline.DoesNotExist:
            raise
        create_date = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        name = "Run %s: %s" % (pipeline.name, create_date)
        if self.name:
            name = self.name + " (" + create_date + ")"
        run = Run(
            run_type=pipeline.pipeline_type,
            name=name,
            app=pipeline,
            status=RunStatus.CREATING,
            job_statuses=dict(),
            output_metadata=self.output_metadata,
            tags=self.tags,
            notify_for_outputs=self.notify_for_outputs,
            resume=self.resume,
        )
        if self.output_directory:
            run.output_directory = self.output_directory
        try:
            run.operator_run = OperatorRun.objects.get(id=self.operator_run_id)
        except OperatorRun.DoesNotExist:
            pass
        try:
            run.job_group = JobGroup.objects.get(id=self.job_group_id)
        except JobGroup.DoesNotExist:
            print("[JobGroup] %s" % self.job_group_id)
        try:
            run.job_group_notifier = JobGroupNotifier.objects.get(id=self.job_group_notifier_id)
        except JobGroupNotifier.DoesNotExist:
            print("[JobGroupNotifier] Not found %s" % self.job_group_notifier_id)
        run.save()
        return run

    def is_valid(self):
        return True
