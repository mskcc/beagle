import uuid
from enum import IntEnum
from django.db import models
from file_system.models import File, FileGroup
from django.contrib.postgres.fields import JSONField
from beagle_etl.models import Operator


class RunStatus(IntEnum):
    CREATING = 0
    READY = 1
    RUNNING = 2
    FAILED = 3
    COMPLETED = 4


class PortType(IntEnum):
    INPUT = 0
    OUTPUT = 1


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


class Run(BaseModel):
    name = models.CharField(max_length=400, editable=True)
    app = models.ForeignKey(Pipeline, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus])
    execution_id = models.UUIDField(null=True, blank=True)
    job_statuses = JSONField(default=dict, blank=True)
    output_metadata = JSONField(default=dict, blank=True, null=True)
    tags = JSONField(default=dict, blank=True, null=True)


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
