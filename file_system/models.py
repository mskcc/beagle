import os
import uuid
from enum import IntEnum
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from notifier.models import JobGroupNotifier
from django.db.models.signals import post_save


class StorageType(IntEnum):
    LOCAL = 0
    AWS_S3 = 1


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Storage(BaseModel):
    name = models.CharField(max_length=20)
    type = models.IntegerField(choices=[(storage_type.value, storage_type.name) for storage_type in StorageType])

    def __repr__(self):
        return "ID: %s NAME: %s TYPE: %s" % (self.id, self.name, StorageType(self.type))

    def __str__(self):
        return u"{}".format(self.name)


class FileType(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return u"{}".format(self.name)


class Request(BaseModel):
    request_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)


class Sample(BaseModel):
    sample_id = models.CharField(max_length=32, unique=True, null=False, blank=False)
    sample_name = models.CharField(max_length=100, null=True, blank=True)
    cmo_sample_name = models.CharField(max_length=100, null=True, blank=True)
    redact = models.BooleanField(default=False, null=False)


class Patient(BaseModel):
    patient_id = models.CharField(max_length=100, unique=True, null=True, blank=True)


class FileExtension(models.Model):
    extension = models.CharField(max_length=30, unique=True)
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE)

    def __str__(self):
        return u"{}".format(self.extension)


class FileGroup(BaseModel):
    name = models.CharField(max_length=40, editable=True)
    slug = models.SlugField(unique=True)
    storage = models.ForeignKey(Storage, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FileGroup, self).save(*args, **kwargs)

    def __str__(self):
        return u"{}".format(self.name)


class FileGroupMetadata(BaseModel):
    file_group = models.ForeignKey(FileGroup, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict, blank=True, null=True)


class File(BaseModel):
    file_name = models.CharField(max_length=500)
    path = models.CharField(max_length=1500, unique=True, db_index=True)
    file_type = models.ForeignKey(FileType, null=True, on_delete=models.SET_NULL)
    size = models.BigIntegerField()
    file_group = models.ForeignKey(FileGroup, on_delete=models.CASCADE)
    checksum = models.CharField(max_length=50, blank=True, null=True)
    request = models.ForeignKey(Request, null=True, on_delete=models.SET_NULL)
    sample = models.ForeignKey(Sample, null=True, on_delete=models.SET_NULL)
    patient = models.ForeignKey(Patient, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if not self.size:
            try:
                self.size = os.path.getsize(self.path)
            except Exception as e:
                self.size = 0
        super(File, self).save(*args, **kwargs)


class ImportMetadata(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    metadata = JSONField(default=dict)


class FileMetadata(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    version = models.IntegerField()
    latest = models.BooleanField()
    metadata = JSONField(default=dict)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        do_not_version = kwargs.pop('do_not_version', False)
        if do_not_version:
            super(FileMetadata, self).save(*args, **kwargs)
        else:
            request_id = self.metadata.get(settings.REQUEST_ID_METADATA_KEY)
            sample_id = self.metadata.get(settings.SAMPLE_ID_METADATA_KEY)
            sample_name = self.metadata.get(settings.SAMPLE_NAME_METADATA_KEY)
            cmo_sample_name = self.metadata.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
            patient_id = self.metadata.get(settings.PATIENT_ID_METADATA_KEY)
            if sample_id:
                if not self.file.sample:
                    sample, _ = Sample.objects.get_or_create(sample_id=sample_id,
                                                          defaults={'cmo_sample_name': cmo_sample_name,
                                                                    'sample_name': sample_name})

                    self.file.sample = sample
                    self.file.save(update_fields=('sample',))
                else:
                    self.file.sample.sample_id = sample_id
                    self.file.sample.sample_name = sample_name
                    self.file.sample.cmo_sample_name = cmo_sample_name
                    self.file.sample.save()

            if request_id:
                if not self.file.request:
                    request, _ = Request.objects.get_or_create(request_id=request_id)

                    self.file.request = request
                    self.file.save(update_fields=('request',))
                else:
                    self.file.request.request_id = request_id
                    self.file.request.save()

            if patient_id:
                if not self.file.patient:
                    patient, _ = Patient.objects.get_or_create(patient_id=patient_id)
                    self.file.patient = patient
                    self.file.save(update_fields=('patient',))
                else:
                    self.file.patient.patient_id = patient_id
                    self.file.patient.save()
            versions = FileMetadata.objects.filter(file_id=self.file.id).values_list('version', flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = FileMetadata.objects.filter(file_id=self.file.id).order_by('-created_date').first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            super(FileMetadata, self).save(*args, **kwargs)

    @staticmethod
    def post_save(sender, **kwargs):
        instance = kwargs.get('instance')
        request_id = instance.metadata.get('requestId')
        pi = instance.metadata.get('labHeadName')
        investigator = instance.metadata.get('investigatorName')
        assay = instance.metadata.get('recipe')
        job_group_notifiers = JobGroupNotifier.objects.filter(request_id=request_id)
        for job_group_notifier in job_group_notifiers:
            job_group_notifier.PI = pi
            job_group_notifier.investigator = investigator
            job_group_notifier.assay = assay
            job_group_notifier.save()

    class Meta:
        indexes = [
            models.Index(
                fields=['version'],
                name='version_idx',
            ),
            GinIndex(
                fields=['metadata'],
                name='metadata_gin',
            ),
        ]


post_save.connect(FileMetadata.post_save, sender=FileMetadata)


class FileRunMap(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    run = JSONField(default=list)

