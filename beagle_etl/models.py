import uuid
import logging
from enum import IntEnum
from django.db import models
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField, ArrayField
from file_system.models import File
from beagle_etl.jobs.helper_jobs import calculate_checksum
from notifier.tasks import notifier_start
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
    gene_panel = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField()
    log = models.TextField(blank=True, null=True, default="")
    sample_status = JSONField(blank=True, default=dict)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in SmileMessageStatus],
        default=SmileMessageStatus.PENDING,
        db_index=True,
    )

    def in_progress(self):
        self.status = SmileMessageStatus.IN_PROGRESS
        job_group = JobGroup.objects.create()
        self.job_group = job_group
        job_group_notifier_id = notifier_start(job_group, self.request_id)
        job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id) if job_group_notifier_id else None
        self.job_group_notifier = job_group_notifier
        self.save(update_fields=["job_group", "job_group_notifier", "status"])

    def copy_files(self):
        self.status = SmileMessageStatus.COPY_FILES
        self.save(update_fields=["status"])

    def complete(self):
        self.status = SmileMessageStatus.COMPLETED
        self.save(update_fields=["status"])

    def not_supported(self):
        self.status = SmileMessageStatus.NOT_SUPPORTED
        self.save(update_fields=["status"])

    def failed(self):
        self.status = SmileMessageStatus.FAILED
        self.save(update_fields=["status"])

    def add_log(self, message):
        self.log += f"{message}\n"
        self.save(update_fields=["log"])

    def set_gene_panel(self, gene_panel):
        self.gene_panel = gene_panel
        self.save(update_fields=["gene_panel"])

    def set_sample_status(self, samples):
        self.sample_status = samples
        self.save(update_fields=["sample_status"])


class RequestCallbackJobStatus(IntEnum):
    PENDING = 0
    COMPLETED = 1


class RequestCallbackJob(BaseModel):
    request_id = models.CharField(max_length=100)
    smile_message = models.ForeignKey(SMILEMessage, null=True, blank=True, on_delete=models.SET_NULL)
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

