import uuid
from enum import IntEnum
from django.db import models
from file_system.models import Request, Sample
from beagle_etl.models import Operator, JobGroup


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class Study(models.Model):
    study_id = models.CharField(max_length=40, null=False)
    requests = models.ManyToManyField(Request)
    samples = models.ManyToManyField(Sample)


class JobGroupWatcherConfig(models.Model):
    name = models.CharField(max_length=20, null=False, blank=False)
    operators = models.ManyToManyField(Operator, related_name="operators")
    post_processors = models.ManyToManyField(Operator, related_name="post_processors")


class JobGroupWatcherStatus(IntEnum):
    WAITING = 0
    RUNNING = 1
    COMPLETED = 2


class JobGroupWatcher(BaseModel):
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in JobGroupWatcherStatus],
        default=JobGroupWatcherStatus.WAITING,
        db_index=True,
    )
    study = models.ForeignKey(Study, null=True, blank=True, on_delete=models.SET_NULL)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    config = models.ForeignKey(JobGroupWatcherConfig, null=False, blank=False, on_delete=models.CASCADE)
