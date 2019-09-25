import uuid
from enum import IntEnum
from django.db import models
from django.contrib.postgres.fields import JSONField


class JobStatus(IntEnum):
    CREATED = 0
    PROCESSED = 1
    FAILED = 2


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)


class JobBaseModel(BaseModel):
    status = models.IntegerField(choices=[(status.value, status.name) for status in JobStatus])


class RequestFetchJob(JobBaseModel):
    request_id = models.CharField(max_length=40)
    data = JSONField(default=dict)


class SamplesFetchJob(JobBaseModel):
    sample_id = models.CharField(max_length=40)
    data = JSONField(default=dict)


class ETLError(BaseModel):
    job_id = models.UUIDField()
    error = JSONField(default=dict, null=True)
