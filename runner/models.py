import uuid
from enum import IntEnum
from django.db import models
from django.contrib.postgres.fields import JSONField


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


class Run(BaseModel):
    name = models.CharField(max_length=100, editable=True)
    app = models.ForeignKey(Pipeline, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=[(status.value, status.name) for status in RunStatus])
    execution_id = models.UUIDField(null=True, blank=True)
    job_statuses = JSONField(default=dict, blank=True)


class Port(BaseModel):
    run = models.ForeignKey(Run, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, editable=True)
    port_type = models.IntegerField(choices=[(port_type.value, port_type.name) for port_type in PortType])
    schema = JSONField()
    value = JSONField(null=True)


class ExecutionEvents(BaseModel):
    execution_id = models.UUIDField()
    name = models.CharField(max_length=100)
    job_status = models.CharField(max_length=30)
    message = models.CharField(max_length=1000)
    err_file_path = models.CharField(max_length=200)
    outputs = JSONField(null=True)
    processed = models.BooleanField(default=False)
