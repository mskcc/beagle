import uuid
from enum import IntEnum
from django.db import models
from file_system.models import File, FileGroup
from django.contrib.postgres.fields import JSONField
from beagle_etl.models import Operator
from django.db.models import F


class RunStatus(IntEnum):
    CREATING = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    COMPLETED = 4


class PortType(IntEnum):
    INPUT = 0
    OUTPUT = 1


class TriggerConditionType(IntEnum):
    NINTY_PERCENT_SUCCEEDED = 0
    ALL_RUNS_SUCCEEDED = 1


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True)
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
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return u"{}".format(self.name)


class OperatorTrigger(BaseModel):
    from_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="from_triggers")
    to_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="to_triggers")
    condition = models.IntegerField(choices=[(t.value, t.name) for t in TriggerConditionType])

    def __str__(self):
        return u"{} -> {} when {}".format(self.from_operator, self.to_operator, TriggerConditionType(self.condition).name.title())

class OperatorRun(BaseModel):
    trigger = models.ForeignKey(OperatorTrigger, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus], default=RunStatus.CREATING)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    num_total_runs = models.IntegerField(null=False)
    num_completed_runs = models.IntegerField(null=False, default=0)
    num_failed_runs = models.IntegerField(null=False, default=0)

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
        return float("{0:.2f}".format(self.num_completed_runs / self.num_total_runs * 100.0))

    @property
    def percent_runs_finished(self):
        return float("{0:.2f}".format((self.num_failed_runs + self.num_completed_runs) / self.num_total_runs * 100.0))


class Run(BaseModel):
    name = models.CharField(max_length=400, editable=True)
    app = models.ForeignKey(Pipeline, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus])
    execution_id = models.UUIDField(null=True, blank=True)
    job_statuses = JSONField(default=dict, blank=True)
    output_metadata = JSONField(default=dict, blank=True, null=True)
    tags = JSONField(default=dict, blank=True, null=True)
    operator_run = models.ForeignKey(OperatorRun, on_delete=models.CASCADE, null=True, related_name="runs")

    def __init__(self, *args, **kwargs):
        super(Run, self).__init__(*args, **kwargs)
        # TODO change state can be handled with a mixin
        self.original = {
            "status": self.status
        }

    def save(self, *args, **kwargs):
        # TODO do we want to decrement if a job goes from completed/failed to open or failed to complete?
        # We can also a prevent a job from going to open once it's in a closed state
        if self.operator_run and self.original["status"] != self.status:
            if self.status == RunStatus.COMPLETED:
                self.operator_run.increment_completed_run()
                self.original["status"] = RunStatus.COMPLETED
            elif self.status == RunStatus.FAILED:
                self.operator_run.increment_failed_run()
                self.original["status"] = RunStatus.FAILED

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


class ExecutionEvents(BaseModel):
    execution_id = models.UUIDField()
    name = models.CharField(max_length=100)
    job_status = models.CharField(max_length=30)
    message = models.CharField(max_length=1000)
    err_file_path = models.CharField(max_length=200)
    outputs = JSONField(null=True)
    processed = models.BooleanField(default=False)


class FileJobTracker(models.Model):
    job = models.ForeignKey(Run, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)


class OperatorErrors(BaseModel):
    operator_name = models.CharField(max_length=100)
    request_id = models.CharField(max_length=100)
    error = JSONField(null=True, blank=True)
