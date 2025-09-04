import uuid
import logging
from enum import IntEnum
from django.db import models
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField, ArrayField
from beagle_etl.metadata.normalizer import Normalizer
from notifier.models import Notifier, JobGroup, JobGroupNotifier


logger = logging.getLogger()


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


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
    IN_PROGRESS = 1
    COPY_FILES = 2
    COMPLETED = 3
    NOT_SUPPORTED = 4
    FAILED = 5


class SMILEMessage(BaseModel):
    topic = models.CharField(max_length=1000)
    request_id = models.CharField(max_length=100)
    message = models.TextField()
    log = models.TextField(blank=True, default="")
    sample_status = JSONField(blank=True, default=dict)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in SmileMessageStatus],
        default=SmileMessageStatus.PENDING,
        db_index=True,
    )


class CopyFileStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1
    FAILED = 2


class CopyFileTask(BaseModel):
    smile_message = models.ForeignKey(SMILEMessage, null=True, blank=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=2000, null=False, blank=False)
    destination = models.CharField(max_length=2000, null=False, blank=False)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in CopyFileStatus],
        default=CopyFileStatus.PENDING,
        db_index=True,
    )

    def set_completed(self, message):
        try:
            with transaction.atomic():
                copy_file_tasks = CopyFileTask.objects.select_for_update().filter(smile_message=self.smile_message)
                self.status = CopyFileStatus.COMPLETED
                self.smile_message.log += f"{message}\n"
                self.save()
                if not copy_file_tasks.filter(status=CopyFileStatus.PENDING).exists():
                    if copy_file_tasks.filter(status=CopyFileStatus.COMPLETED).count() == copy_file_tasks.count():
                        self.smile_message.status = SmileMessageStatus.COMPLETED
                    else:
                        self.smile_message.status = SmileMessageStatus.FAILED
                self.smile_message.save()
        except IntegrityError as e:
            logger.error(f"Integrity error {e}")

    def set_failed(self, message=""):
        try:
            with transaction.atomic():
                copy_file_tasks = CopyFileTask.objects.select_for_update().filter(smile_message=self.smile_message)
                self.status = CopyFileStatus.FAILED
                self.smile_message.log += f"{message}\n"
                self.save()
                if not copy_file_tasks.filter(status=CopyFileStatus.PENDING).exists():
                    self.smile_message.status = SmileMessageStatus.FAILED
                self.smile_message.save()
        except IntegrityError as e:
            logger.error(f"Integrity error {e}")


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
