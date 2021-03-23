import os
import uuid
from enum import IntEnum
from django.db import models
from django.db.models import F
from file_system.models import File, FileGroup, Sample
from beagle_etl.models import Operator, JobGroup, JobGroupNotifier
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.utils.timezone import now


class RunType(IntEnum):
    CWL = 0
    NEXTFLOW = 1


class RunStatus(IntEnum):
    CREATING = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    COMPLETED = 4
    ABORTED = 5


class PortType(IntEnum):
    INPUT = 0
    OUTPUT = 1


# Triggers on an aggregate (some amount of run threshold must be met) or on
# an individual run
class TriggerRunType(IntEnum):
    AGGREGATE = 0
    INDIVIDUAL = 1


class TriggerAggregateConditionType(IntEnum):
    NINTY_PERCENT_SUCCEEDED = 0
    ALL_RUNS_SUCCEEDED = 1


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Pipeline(BaseModel):
    name = models.CharField(max_length=100, editable=True)
    github = models.CharField(max_length=300, editable=True)
    version = models.CharField(max_length=100, editable=True)
    entrypoint = models.CharField(max_length=100, editable=True)
    output_file_group = models.ForeignKey(FileGroup, on_delete=models.CASCADE)
    output_directory = models.CharField(max_length=300, null=True, editable=True)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    default = models.BooleanField(default=False)

    @property
    def pipeline_link(self):
        return '{github}/blob/{version}/{entrypoint}'.format(github=self.github,
                                                             version=self.version,
                                                             entrypoint=self.entrypoint)

    def __str__(self):
        return u"{}".format(self.name)


class OperatorTrigger(BaseModel):
    from_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="from_triggers")
    to_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="to_triggers")
    aggregate_condition = models.IntegerField(choices=[(t.value, t.name) for t in TriggerAggregateConditionType], null=True)
    run_type = models.IntegerField(choices=[(t.value, t.name) for t in TriggerRunType])

    def __str__(self):
        if self.run_type == TriggerRunType.AGGREGATE:
            return u"{} -> {} when {}".format(self.from_operator, self.to_operator,
                                              TriggerAggregateConditionType(self.aggregate_condition).name.title())
        elif self.run_type == TriggerRunType.INDIVIDUAL:
            return u"{} -> {} on each run".format(self.from_operator, self.to_operator)
        else:
            return u"{} -> {}".format(self.from_operator, self.to_operator)


class OperatorRun(BaseModel):
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus],
                                 default=RunStatus.CREATING, db_index=True)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    num_total_runs = models.IntegerField(null=False)
    num_completed_runs = models.IntegerField(null=False, default=0)
    num_failed_runs = models.IntegerField(null=False, default=0)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
    finished_date = models.DateTimeField(blank=True, null=True, db_index=True)
    parent = models.ForeignKey('self', default=None, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        if self.status == RunStatus.COMPLETED or self.status == RunStatus.FAILED:
            if not self.finished_date:
                self.finished_date = now()
        super().save(*args, **kwargs)

    def complete(self):
        self.status = RunStatus.COMPLETED
        self.save()

    def fail(self):
        self.status = RunStatus.FAILED
        self.save()

    def increment_failed_run(self):
        self.num_failed_runs = F('num_failed_runs') + 1
        self.save()

    def increment_completed_run(self):
        self.num_completed_runs = F('num_completed_runs') + 1
        self.save()

    @property
    def percent_runs_succeeded(self):
        if self.num_total_runs > 0:
            return float("{0:.2f}".format(self.num_completed_runs / self.num_total_runs * 100.0))
        else:
            return float(0)

    @property
    def percent_runs_finished(self):
        if self.num_total_runs > 0:
            return float(
                "{0:.2f}".format((self.num_failed_runs + self.num_completed_runs) / self.num_total_runs * 100.0))
        else:
            return 0

    @property
    def total_runs(self):
        self.refresh_from_db()
        return self.num_total_runs

    @property
    def completed_runs(self):
        self.refresh_from_db()
        return self.num_completed_runs

    @property
    def failed_runs(self):
        self.refresh_from_db()
        return self.num_failed_runs

    @property
    def running_runs(self):
        self.refresh_from_db()
        return self.num_total_runs - (self.num_completed_runs + self.num_failed_runs)


class Run(BaseModel):
    run_type = models.IntegerField(choices=[(run_type.value, run_type.name) for run_type in RunType], db_index=True,
                                   default=RunType.CWL)
    name = models.CharField(max_length=400, editable=True)
    app = models.ForeignKey(Pipeline, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus], db_index=True)
    execution_id = models.UUIDField(null=True, blank=True)
    job_statuses = JSONField(default=dict, blank=True)
    message = JSONField(default=dict, blank=True, null=True)
    output_metadata = JSONField(default=dict, blank=True, null=True)
    output_directory = models.CharField(max_length=1000, editable=True, blank=True, null=True)
    tags = JSONField(default=dict, blank=True, null=True)
    operator_run = models.ForeignKey(OperatorRun, on_delete=models.CASCADE, null=True, related_name="runs")
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
    notify_for_outputs = ArrayField(models.CharField(max_length=40, blank=True))
    samples = models.ManyToManyField(Sample)
    started = models.DateTimeField(blank=True, null=True)
    submitted = models.DateTimeField(blank=True, null=True)
    finished_date = models.DateTimeField(blank=True, null=True, db_index=True)
    resume = models.UUIDField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super(Run, self).__init__(*args, **kwargs)
        # TODO change state can be handled with a mixin
        self.original = {
            "status": self.status
        }

    def __str__(self):
        return str(self.pk)

    def clear(self):
        fields_to_clear = ["resume", "finished_date", "started", "output_directory", "message",
                           "execution_id"]
        for f in fields_to_clear:
            setattr(self, f, None)

        self.job_statuses = {}
        self.status = RunStatus.READY
        return self

    @property
    def is_completed(self):
        self.refresh_from_db()
        return self.status == RunStatus.COMPLETED

    def save(self, *args, **kwargs):
        """
        If output directory is set to None, by default assign it to the pipeline output directory
        plus the run id
        """
        if not self.output_directory and self.id:
            pipeline = self.app
            pipeline_output_directory = pipeline.output_directory
            self.output_directory = os.path.join(pipeline_output_directory, str(self.id))
        # TODO do we want to decrement if a job goes from completed/failed to open or failed to complete?
        # We can also a prevent a job from going to open once it's in a closed state
        if self.operator_run and self.original["status"] != self.status:
            if self.status == RunStatus.COMPLETED:
                self.operator_run.increment_completed_run()
                self.original["status"] = RunStatus.COMPLETED
                self.finished_date = now()
            elif self.status == RunStatus.FAILED:
                self.operator_run.increment_failed_run()
                self.original["status"] = RunStatus.FAILED
                self.finished_date = now()
        super(Run, self).save(*args, **kwargs)


class Port(BaseModel):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, editable=True)
    port_type = models.IntegerField(choices=[(port_type.value, port_type.name) for port_type in PortType])
    schema = JSONField(null=True, blank=True)
    secondary_files = JSONField(null=True, blank=True)
    db_value = JSONField(null=True)
    value = JSONField(null=True)
    files = models.ManyToManyField(File)
    notify = models.BooleanField(default=False)


class ExecutionEvents(BaseModel):
    execution_id = models.UUIDField()
    name = models.CharField(max_length=100)
    job_status = models.CharField(max_length=30)
    message = models.CharField(max_length=1000)
    err_file_path = models.CharField(max_length=200)
    outputs = JSONField(null=True)
    processed = models.BooleanField(default=False)


class FileJobTracker(models.Model):
    """
    TODO: FileJobTracker Deprecated. Remove model in the future
    """
    job = models.ForeignKey(Run, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)


class OperatorErrors(BaseModel):
    operator_name = models.CharField(max_length=100)
    request_id = models.CharField(max_length=100)
    error = JSONField(null=True, blank=True)
