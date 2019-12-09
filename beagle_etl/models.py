import uuid
from enum import IntEnum
from django.db import models
from runner.models import Pipeline
from django.contrib.postgres.fields import JSONField


class JobStatus(IntEnum):
    CREATED = 0
    IN_PROGRESS = 1
    WAITING_FOR_CHILDREN = 2
    COMPLETED = 3
    FAILED = 4


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)


class Job(BaseModel):
    run = models.CharField(max_length=100)
    args = JSONField(null=True, blank=True)
    status = models.IntegerField(choices=[(status.value, status.name) for status in JobStatus])
    children = JSONField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    message = JSONField(null=True, blank=True)
    max_retry = models.IntegerField(default=3)
    callback = models.CharField(max_length=100, default=None, blank=True)
    callback_args = JSONField(null=True, blank=True)
    lock = models.BooleanField(default=False)


class Operator(models.Model):
    active = models.BooleanField(default=False)
