import uuid
from enum import IntEnum
from notifier.models import JobGroup
from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.utils.timezone import now

class JobStatus(IntEnum):
    CREATED = 0
    IN_PROGRESS = 1
    WAITING_FOR_CHILDREN = 2
    COMPLETED = 3
    FAILED = 4


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class Job(BaseModel):
    run = models.CharField(max_length=100, db_index=True)
    args = JSONField(null=True, blank=True)
    status = models.IntegerField(choices=[(status.value, status.name) for status in JobStatus], db_index=True)
    children = JSONField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    message = JSONField(null=True, blank=True)
    max_retry = models.IntegerField(default=3)
    callback = models.CharField(max_length=100, default=None, blank=True, null=True)
    callback_args = JSONField(null=True, blank=True)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    lock = models.BooleanField(default=False)
    finished_date = models.DateTimeField(blank=True, null=True, db_index=True)
    def save(self, *args, **kwargs):
        if self.status == JobStatus.COMPLETED or self.status == JobStatus.FAILED:
            if not self.finished_date:
                self.finished_date = now()
        super().save(*args, **kwargs)

    @property
    def is_locked(self):
        self.refresh_from_db()
        return self.lock

    def lock_job(self):
        self.lock = True
        self.save()

    def unlock_job(self):
        self.lock = False
        self.save()


class Operator(models.Model):
    slug = models.CharField(max_length=100, default=False)
    class_name = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    recipes = ArrayField(models.CharField(max_length=50, default=False))

    def __str__(self):
        return u"{}".format(self.slug)


class Assay(models.Model):
    all = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    disabled = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    hold = ArrayField(models.CharField(max_length=100), null=True, blank=True)
