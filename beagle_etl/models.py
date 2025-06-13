import uuid
from enum import IntEnum
from notifier.models import Notifier, JobGroup, JobGroupNotifier
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField, ArrayField
from django.utils.timezone import now
from beagle_etl.metadata.normalizer import Normalizer


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
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
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
    class_name = models.CharField(max_length=150)
    version = models.CharField(max_length=50)
    active = models.BooleanField(default=False)
    recipes = ArrayField(models.CharField(max_length=50, default=False))
    recipes_json = JSONField(default=list, null=True)
    notifier = models.ForeignKey(Notifier, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.slug)


class ETLConfiguration(models.Model):
    redelivery = models.BooleanField(default=True)
    all_recipes = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    disabled_recipes = ArrayField(models.CharField(max_length=100), null=True, blank=True)
    hold_recipes = ArrayField(models.CharField(max_length=100), null=True, blank=True)


class SkipProject(models.Model):
    skip_projects = ArrayField(models.CharField(max_length=100), null=True, blank=True)


class SmileMessageStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1
    NOT_SUPPORTED = 2
    FAILED = 3


class SMILEMessage(BaseModel):
    topic = models.CharField(max_length=1000)
    request_id = models.CharField(max_length=100)
    message = models.TextField()
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in SmileMessageStatus],
        default=SmileMessageStatus.PENDING,
        db_index=True,
    )


class RequestCallbackJobStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1


class RequestCallbackJob(BaseModel):
    request_id = models.CharField(max_length=100)
    recipe = models.CharField(max_length=100)
    fastq_metadata = JSONField(default=dict)
    samples = JSONField(null=True, blank=True)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in RequestCallbackJobStatus],
        default=SmileMessageStatus.PENDING,
        db_index=True,
    )
    delay = models.IntegerField(default=0)


class NormalizerModel(BaseModel):
    condition = JSONField(null=False, blank=False)
    normalizer = JSONField(null=False, blank=False)


def initialize_normalizer():
    normalizers = []
    for normalizer in NormalizerModel.objects.all():
        normalizers.append(Normalizer(normalizer.condition, normalizer.normalizer))
    return normalizers


class ValidatorModel(BaseModel):
    name = models.CharField(null=False, blank=False, max_length=30, default="Metadata Schema")
    schema = JSONField(null=False, blank=False)

    def save(self, *args, **kwargs):
        if not self.pk and ValidatorModel.objects.exists():
            raise ValidationError("There is can be only one ValidatorModel instance")
        return super(ValidatorModel, self).save(*args, **kwargs)


def get_metadata_schema():
    return ValidatorModel.objects.first()
