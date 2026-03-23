import logging
import datetime
from django.conf import settings
from notifier.models import JobGroup, JobGroupNotifier
from runner.models import Pipeline, Run, RunStatus, OperatorRun


class RunCreator(object):
    logger = logging.getLogger(__name__)

    def create(self):
        # TODO: Creating of Run object should be in different class so RunCreator could be moved to voyager_operator
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
            log_prefix=self.log_prefix,
            log_directory=self.log_directory,
        )
        if self.output_directory:
            run.output_directory = self.output_directory
        if pipeline.log_directory:
            run.log_directory = pipeline.log_directory
        try:
            run.operator_run = OperatorRun.objects.get(id=self.operator_run_id)
        except OperatorRun.DoesNotExist:
            pass
        try:
            run.job_group = JobGroup.objects.get(id=self.job_group_id)
        except JobGroup.DoesNotExist:
            run.job_group = JobGroup.objects.create()
            print("[JobGroup] %s" % self.job_group_id)
        try:
            run.job_group_notifier = JobGroupNotifier.objects.get(id=self.job_group_notifier_id)
        except JobGroupNotifier.DoesNotExist:
            print("[JobGroupNotifier] Not found %s" % self.job_group_notifier_id)
        run.save()
        return run

    def __init__(
        self,
        # TODO: app should be pipeline github repo and version
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
        log_prefix="",
        log_directory=settings.DEFAULT_LOG_PATH,
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
        self.log_prefix = log_prefix
        self.log_directory = log_directory
        self.resume = resume

    def is_valid(self):
        return True
