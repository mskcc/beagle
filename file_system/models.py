import os
import uuid
from enum import IntEnum
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex

# from file_system.serializers import UpdateFileSerializer
from file_system.tasks import populate_job_group_notifier_metadata


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
        return "{}".format(self.name)


class FileType(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return "{}".format(self.name)


class Request(BaseModel):
    request_id = models.CharField(max_length=100, null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    lab_head_name = models.CharField(max_length=200, null=True, blank=True)
    investigator_email = models.CharField(max_length=200, null=True, blank=True)
    investigator_name = models.CharField(max_length=200, null=True, blank=True)
    version = models.IntegerField()
    latest = models.BooleanField()

    def _update_files(self, request_id, updated_metadata):
        query = {f"metadata__{settings.REQUEST_ID_METADATA_KEY}": request_id}
        files = FileMetadata.objects.filter(**query)
        for f in files:
            for k, v in updated_metadata.items():
                f.metadata[k] = v
            f.save(skip_request_sample_patient_update=True)

    def save(self, *args, **kwargs):
        do_not_version = kwargs.pop("do_not_version", False)
        update_files = False
        if hasattr(self, "update_files"):
            update_files = self.update_files
        if do_not_version:
            super(Request, self).save(*args, **kwargs)
        else:
            versions = Request.objects.filter(request_id=self.request_id).values_list("version", flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = Request.objects.filter(request_id=self.request_id).order_by("-created_date").first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            metadata = {
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                settings.LAB_HEAD_NAME_METADATA_KEY: self.lab_head_name,
                settings.INVESTIGATOR_EMAIL_METADATA_KEY: self.investigator_email,
                settings.INVESTIGATOR_NAME_METADATA_KEY: self.investigator_name,
            }
            if update_files:
                self._update_files(self.request_id, metadata)
            super(Request, self).save(*args, **kwargs)


class Sample(BaseModel):
    sample_id = models.CharField(max_length=32, null=False, blank=False)
    sample_name = models.CharField(max_length=100, null=True, blank=True)
    cmo_sample_name = models.CharField(max_length=100, null=True, blank=True)
    sample_type = models.CharField(max_length=100, null=True, blank=True)
    tumor_or_normal = models.CharField(max_length=30, null=True, blank=True)
    sample_class = models.CharField(max_length=30, null=True, blank=True)
    redact = models.BooleanField(default=False, null=False)
    version = models.IntegerField()
    latest = models.BooleanField()

    def _update_files(self, sample_id, updated_metadata):
        query = {f"metadata__{settings.SAMPLE_ID_METADATA_KEY}": sample_id}
        files = FileMetadata.objects.filter(**query)
        for f in files:
            for k, v in updated_metadata.items():
                f.metadata[k] = v
            f.save(skip_request_sample_patient_update=True)

    def save(self, *args, **kwargs):
        do_not_version = kwargs.pop("do_not_version", False)
        update_files = False
        if hasattr(self, "update_files"):
            update_files = self.update_files
        if do_not_version:
            super(Sample, self).save(*args, **kwargs)
        else:
            versions = Sample.objects.filter(sample_id=self.sample_id).values_list("version", flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = Sample.objects.filter(sample_id=self.sample_id).order_by("-created_date").first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            if update_files:
                metadata = {
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: self.cmo_sample_name,
                    settings.SAMPLE_NAME_METADATA_KEY: self.sample_name,
                    settings.CMO_SAMPLE_CLASS_METADATA_KEY: self.sample_type,
                    settings.SAMPLE_CLASS_METADATA_KEY: self.sample_class,
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: self.tumor_or_normal,
                }
                self._update_files(self.sample_id, metadata)
            super(Sample, self).save(*args, **kwargs)


class Patient(BaseModel):
    patient_id = models.CharField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=30, null=True, blank=True)
    version = models.IntegerField()
    latest = models.BooleanField()

    class Meta:
        select_on_save = True

    def _update_files(self, patient_id, updated_metadata):
        query = {f"metadata__{settings.PATIENT_ID_METADATA_KEY}": patient_id}
        files = FileMetadata.objects.filter(**query)
        for f in files:
            for k, v in updated_metadata.items():
                f.metadata[k] = v
            f.save(skip_request_sample_patient_update=True)

    def save(self, *args, **kwargs):
        do_not_version = kwargs.pop("do_not_version", False)
        update_files = False
        if hasattr(self, "update_files"):
            update_files = self.update_files
        if do_not_version:
            super(Patient, self).save(*args, **kwargs)
        else:
            versions = Patient.objects.filter(patient_id=self.patient_id).values_list("version", flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = Patient.objects.filter(patient_id=self.patient_id).order_by("-created_date").first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            if update_files:
                metadata = {settings.SEX_METADATA_KEY: self.sex}
                self._update_files(self.patient_id, metadata)
            super(Patient, self).save(*args, **kwargs)


class FileExtension(models.Model):
    extension = models.CharField(max_length=30, unique=True)
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.extension)


class FileGroup(BaseModel):
    name = models.CharField(max_length=40, editable=True)
    slug = models.SlugField(unique=True)
    storage = models.ForeignKey(Storage, blank=True, null=True, on_delete=models.SET_NULL)
    default = models.BooleanField(default=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FileGroup, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.name)


class FileGroupMetadata(BaseModel):
    file_group = models.ForeignKey(FileGroup, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict, blank=True, null=True)


class File(BaseModel):
    file_name = models.CharField(max_length=500)
    path = models.CharField(max_length=1500, db_index=True)
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
        do_not_version = kwargs.pop("do_not_version", False)
        # Skip updating Request, Sample or Patient objects
        skip_request_sample_patient_update = kwargs.pop("skip_request_sample_patient_update", False)
        if do_not_version:
            super(FileMetadata, self).save(*args, **kwargs)
        else:
            request_id = self.metadata.get(settings.REQUEST_ID_METADATA_KEY)
            lab_head_name = self.metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY)
            investigator_email = self.metadata.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY)
            investigator_name = self.metadata.get(settings.INVESTIGATOR_NAME_METADATA_KEY)

            sample_id = self.metadata.get(settings.SAMPLE_ID_METADATA_KEY)
            sample_name = self.metadata.get(settings.SAMPLE_NAME_METADATA_KEY)
            cmo_sample_name = self.metadata.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
            sample_type = self.metadata.get(settings.CMO_SAMPLE_CLASS_METADATA_KEY)
            tumor_or_normal = self.metadata.get(settings.TUMOR_OR_NORMAL_METADATA_KEY)
            sample_class = self.metadata.get(settings.SAMPLE_CLASS_METADATA_KEY)

            patient_id = self.metadata.get(settings.PATIENT_ID_METADATA_KEY)
            sex = self.metadata.get(settings.SEX_METADATA_KEY)

            assay = self.metadata.get(settings.RECIPE_METADATA_KEY, "")
            populate_job_group_notifier_metadata.delay(request_id, lab_head_name, investigator_name, assay)

            if request_id:
                request, _ = Request.objects.get_or_create(
                    request_id=request_id,
                    defaults={
                        "lab_head_name": lab_head_name,
                        "investigator_email": investigator_email,
                        "investigator_name": investigator_name,
                    },
                )
                if not (_ or skip_request_sample_patient_update):
                    request.lab_head_name = lab_head_name
                    request.investigator_email = investigator_email
                    request.investigator_name = investigator_name
                    request.save()
                self.file.request = request
                self.file.save(update_fields=("request",))

            if sample_id:
                sample, _ = Sample.objects.get_or_create(
                    sample_id=sample_id,
                    defaults={
                        "cmo_sample_name": cmo_sample_name,
                        "sample_name": sample_name,
                        "sample_type": sample_type,
                        "tumor_or_normal": tumor_or_normal,
                        "sample_class": sample_class,
                    },
                )
                self.file.sample = sample
                if not (_ or skip_request_sample_patient_update):
                    sample.sample_name = sample_name
                    sample.cmo_sample_name = cmo_sample_name
                    sample.sample_type = sample_type
                    sample.tumor_or_normal = tumor_or_normal
                    sample.sample_class = sample_class
                    sample.save()
                self.file.save(update_fields=("sample",))

            if patient_id:
                patient, _ = Patient.objects.get_or_create(patient_id=patient_id, defaults={"sex": sex})
                if not (_ or skip_request_sample_patient_update):
                    patient.sex = sex
                    patient.save()
                self.file.patient = patient
                self.file.save(update_fields=("patient",))

            versions = FileMetadata.objects.filter(file_id=self.file.id).values_list("version", flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = FileMetadata.objects.filter(file_id=self.file.id).order_by("-created_date").first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            super(FileMetadata, self).save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(
                fields=["version"],
                name="version_idx",
            ),
            GinIndex(
                fields=["metadata"],
                name="metadata_gin",
            ),
        ]


class FileRunMap(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    run = JSONField(default=list)
