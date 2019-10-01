import uuid
from enum import IntEnum
from django.db import models
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
    args = JSONField(null=True)
    status = models.IntegerField(choices=[(status.value, status.name) for status in JobStatus])
    children = JSONField()
    retry_count = models.IntegerField(default=0)
    message = JSONField(null=True)
    max_retry = models.IntegerField(default=3)
