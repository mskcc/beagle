import os
import uuid
import copy
import logging
from datetime import datetime
from enum import IntEnum
from deepdiff import DeepDiff
from django.db import models
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.postgres.fields import JSONField, ArrayField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex
from django.core.exceptions import ValidationError
from file_system.tasks import populate_job_group_notifier_metadata


logger = logging.getLogger(__name__)


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


def update_dict(current, new):
    updated = copy.deepcopy(current)
    for k, v in updated.items():
        if new.get(k):
            updated[k] = new[k]
    return updated


class RequestModelManager(models.Manager):
    @staticmethod
    def extract_from_metadata(metadata):
        return {
            "request_id": metadata.get(settings.REQUEST_ID_METADATA_KEY, None),
            "lab_head_name": metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY, None),
            "lab_head_email": metadata.get(settings.LAB_HEAD_EMAIL_METADATA_KEY, None),
            "investigator_email": metadata.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY, None),
            "investigator_name": metadata.get(settings.INVESTIGATOR_NAME_METADATA_KEY, None),
        }

    def _update_files(self, request_id, updated_metadata, user):
        query = {f"metadata__{settings.REQUEST_ID_METADATA_KEY}": request_id}
        files = FileMetadata.objects.select_for_update().filter(**query)
        metadata = {
            settings.LAB_HEAD_NAME_METADATA_KEY: updated_metadata.get("lab_head_name", None),
            settings.LAB_HEAD_EMAIL_METADATA_KEY: updated_metadata.get("lab_head_email", None),
            settings.INVESTIGATOR_EMAIL_METADATA_KEY: updated_metadata.get("investigator_email", None),
            settings.INVESTIGATOR_NAME_METADATA_KEY: updated_metadata.get("investigator_name", None),
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        for f in files:
            update_body = {"file": f.file.id, "metadata": metadata, "user": user}
            FileMetadata.objects.create_or_update(from_file=False, **update_body)

    def _update_versioned_instance(self, updates, from_file=False, user=None):
        try:
            with transaction.atomic():
                request_id = updates["request_id"]
                objs = Request.objects.select_for_update().filter(request_id=request_id).order_by("-version").all()
                obj = objs.first()
                latest_metadata = {
                    "request_id": obj.request_id,
                    "delivery_date": obj.delivery_date,
                    "lab_head_name": obj.lab_head_name,
                    "lab_head_email": obj.lab_head_email,
                    "investigator_email": obj.investigator_email,
                    "investigator_name": obj.investigator_name,
                }
                # Filter out null values
                updates = {k: v for k, v in updates.items() if v is not None}
                updated_metadata = update_dict(latest_metadata, updates)
                if DeepDiff(updated_metadata, latest_metadata, ignore_order=True):
                    version = obj.version + 1
                    obj.latest = False
                    obj.save()
                    new_request_obj = Request.objects.create(**updated_metadata, latest=True, version=version)
                    if not from_file:
                        self._update_files(request_id, updated_metadata, user)
                    logger.debug(f"Request {request_id} updated {str(new_request_obj)}")
                    return new_request_obj
                else:
                    logger.debug(f"No updates {str(obj)}")
                    return obj
        except IntegrityError as e:
            logger.debug(f"Integrity error {e}")
            return self._update_versioned_instance(updates, from_file, user)

    def create_or_update_instance(
        self,
        request_id,
        delivery_date=None,
        lab_head_name=None,
        lab_head_email=None,
        investigator_name=None,
        investigator_email=None,
        from_file=False,
        user=None,
    ):
        current = {
            "request_id": request_id,
            "delivery_date": delivery_date,
            "lab_head_name": lab_head_name,
            "lab_head_email": lab_head_email,
            "investigator_name": investigator_name,
            "investigator_email": investigator_email,
        }
        obj, created = Request.objects.get_or_create(request_id=request_id, latest=True, defaults=current)
        if not created:
            return self._update_versioned_instance(current, from_file, user)
        else:
            return obj


class Request(BaseModel):
    request_id = models.CharField(max_length=100, null=False, blank=False)
    delivery_date = models.DateTimeField(null=True, blank=True)
    lab_head_name = models.CharField(max_length=200, null=True, blank=True)
    lab_head_email = models.CharField(max_length=200, null=True, blank=True)
    investigator_name = models.CharField(max_length=200, null=True, blank=True)
    investigator_email = models.CharField(max_length=200, null=True, blank=True)
    version = models.IntegerField(default=0)
    latest = models.BooleanField(default=True)

    objects = RequestModelManager()

    def __str__(self):
        return f"{self.request_id} {self.version} {self.latest}"

    class Meta:
        unique_together = ("request_id", "version")


class SampleModelManager(models.Manager):
    @staticmethod
    def extract_from_metadata(metadata):
        return {
            "sample_id": metadata.get(settings.SAMPLE_ID_METADATA_KEY, None),
            "sample_name": metadata.get(settings.CMO_SAMPLE_NAME_METADATA_KEY, None),
            "cmo_sample_name": metadata.get(settings.SAMPLE_NAME_METADATA_KEY, None),
            "sample_type": metadata.get(settings.CMO_SAMPLE_CLASS_METADATA_KEY, None),
            "tumor_or_normal": metadata.get(settings.TUMOR_OR_NORMAL_METADATA_KEY, None),
            "sample_class": metadata.get(settings.SAMPLE_CLASS_METADATA_KEY, None),
            "request_id": metadata.get(settings.REQUEST_ID_METADATA_KEY, None),
        }

    def _update_files(self, sample_id, updated_metadata, user):
        query = {f"metadata__{settings.SAMPLE_ID_METADATA_KEY}": sample_id}
        files = FileMetadata.objects.select_for_update().filter(**query)
        metadata = {
            settings.CMO_SAMPLE_NAME_METADATA_KEY: updated_metadata.get("sample_name", None),
            settings.SAMPLE_NAME_METADATA_KEY: updated_metadata.get("cmo_sample_name", None),
            settings.CMO_SAMPLE_CLASS_METADATA_KEY: updated_metadata.get("sample_type", None),
            settings.TUMOR_OR_NORMAL_METADATA_KEY: updated_metadata.get("tumor_or_normal", None),
            settings.SAMPLE_CLASS_METADATA_KEY: updated_metadata.get("sample_class", None),
            settings.REQUEST_ID_METADATA_KEY: updated_metadata.get("request_id", None),
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        for f in files:
            update_body = {"file": f.file.id, "metadata": metadata, "user": user}
            FileMetadata.objects.create_or_update(from_file=False, **update_body)

    def _update_versioned_instance(self, updates, from_file=False, user=None):
        try:
            with transaction.atomic():
                sample_id = updates["sample_id"]
                objs = Sample.objects.select_for_update().filter(sample_id=sample_id).order_by("-version").all()
                obj = objs.first()
                latest_metadata = {
                    "sample_id": obj.sample_id,
                    "sample_name": obj.sample_name,
                    "cmo_sample_name": obj.cmo_sample_name,
                    "sample_type": obj.sample_type,
                    "tumor_or_normal": obj.tumor_or_normal,
                    "sample_class": obj.sample_class,
                    "igo_qc_notes": obj.igo_qc_notes,
                    "cas_qc_notes": obj.cas_qc_notes,
                    "request_id": obj.request_id,
                    "redact": obj.redact,
                }
                updated_metadata = update_dict(latest_metadata, updates)
                if DeepDiff(updated_metadata, latest_metadata, ignore_order=True):
                    version = obj.version + 1
                    obj.latest = False
                    obj.save()
                    new_sample_obj = Sample.objects.create(**updated_metadata, latest=True, version=version)
                    if not from_file:
                        self._update_files(sample_id, updated_metadata, user)
                    logger.debug(f"Sample {sample_id} updated {str(new_sample_obj)}")
                    return new_sample_obj
                else:
                    logger.debug(f"No updates {str(obj)}")
                    return obj
        except IntegrityError as e:
            logger.debug(f"Integrity error {e}")
            return self._update_versioned_instance(updates, from_file, user)

    def create_or_update_instance(
        self,
        sample_id,
        sample_name=None,
        cmo_sample_name=None,
        sample_type=None,
        tumor_or_normal=None,
        sample_class=None,
        igo_qc_notes="",
        cas_qc_notes="",
        request_id=None,
        redact=False,
        from_file=False,
        user=None,
    ):
        current = {
            "sample_id": sample_id,
            "sample_name": sample_name,
            "cmo_sample_name": cmo_sample_name,
            "sample_type": sample_type,
            "tumor_or_normal": tumor_or_normal,
            "sample_class": sample_class,
            "igo_qc_notes": igo_qc_notes,
            "cas_qc_notes": cas_qc_notes,
            "request_id": request_id,
            "redact": redact,
        }
        obj, created = Sample.objects.get_or_create(sample_id=sample_id, latest=True, defaults=current)
        if not created:
            return self._update_versioned_instance(current, from_file, user)
        else:
            return obj


class Sample(BaseModel):
    sample_id = models.CharField(max_length=32, null=False, blank=False)
    sample_name = models.CharField(max_length=100, null=True, blank=True)
    cmo_sample_name = models.CharField(max_length=100, null=True, blank=True)
    sample_type = models.CharField(max_length=100, null=True, blank=True)
    tumor_or_normal = models.CharField(max_length=30, null=True, blank=True)
    sample_class = models.CharField(max_length=30, null=True, blank=True)
    igo_qc_notes = models.TextField(default="")
    cas_qc_notes = models.TextField(default="")
    request_id = models.CharField(max_length=100, null=True, blank=True)
    redact = models.BooleanField(default=False, null=False)
    version = models.IntegerField(default=0)
    latest = models.BooleanField(default=True)

    objects = SampleModelManager()

    def __str__(self):
        return f"{self.sample_id} {self.version} {self.latest}"

    class Meta:
        unique_together = ("sample_id", "version")


class PatientModelManager(models.Manager):
    @staticmethod
    def extract_from_metadata(metadata):
        return {
            "patient_id": metadata.get(settings.PATIENT_ID_METADATA_KEY, None),
            "sex": metadata.get(settings.SEX_METADATA_KEY, None),
        }

    def _update_files(self, patient_id, updated_metadata, user):
        query = {f"metadata__{settings.PATIENT_ID_METADATA_KEY}": patient_id}
        files = FileMetadata.objects.filter(**query)
        metadata = {
            settings.PATIENT_ID_METADATA_KEY: updated_metadata.get("patient_id", None),
            settings.SEX_METADATA_KEY: updated_metadata.get("sex", None),
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}
        for f in files:
            update_body = {"file": f.file.id, "metadata": metadata, "user": user}
            FileMetadata.objects.create_or_update(from_file=False, **update_body)

    def _update_versioned_instance(self, updates, from_file=False, user=None):
        try:
            with transaction.atomic():
                patient_id = updates["patient_id"]
                objs = Patient.objects.select_for_update().filter(patient_id=patient_id).order_by("-version").all()
                obj = objs.first()
                latest_metadata = {"patient_id": obj.patient_id, "sex": obj.sex, "samples": obj.samples}
                updated_metadata = update_dict(latest_metadata, updates)
                if DeepDiff(updated_metadata, latest_metadata, ignore_order=True):
                    version = obj.version + 1
                    obj.latest = False
                    obj.save()
                    new_patient_obj = Patient.objects.create(**updated_metadata, latest=True, version=version)
                    if not from_file:
                        self._update_files(patient_id, updated_metadata, user)
                    logger.debug(f"Patient {patient_id} updated {str(new_patient_obj)}")
                    return new_patient_obj
                else:
                    logger.debug(f"No updates {str(obj)}")
                    return obj
        except IntegrityError as e:
            logger.debug(f"Integrity error {e}")
            return self._update_versioned_instance(updates, from_file)

    def create_or_update_instance(self, patient_id, sex=None, samples=[], from_file=False, user=None):
        current = {"patient_id": patient_id, "sex": sex, "samples": samples}
        obj, created = Patient.objects.get_or_create(patient_id=current["patient_id"], latest=True, defaults=current)
        if not created:
            return self._update_versioned_instance(current, from_file, user)
        return obj


class Patient(BaseModel):
    patient_id = models.CharField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=30, null=True, blank=True)
    samples = ArrayField(models.CharField(max_length=100), default=list)
    version = models.IntegerField(default=0)
    latest = models.BooleanField(default=True)

    objects = PatientModelManager()

    class Meta:
        select_on_save = True
        unique_together = ("patient_id", "version")


class FileExtension(models.Model):
    extension = models.CharField(max_length=30, unique=True)
    file_type = models.ForeignKey(FileType, on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.extension)


class File(BaseModel):
    file_name = models.CharField(max_length=500)
    path = models.CharField(max_length=1500, db_index=True)
    file_type = models.ForeignKey(FileType, null=True, on_delete=models.SET_NULL)
    size = models.BigIntegerField()
    file_group = models.ForeignKey(FileGroup, on_delete=models.CASCADE)
    checksum = models.CharField(max_length=50, blank=True, null=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    samples = ArrayField(models.CharField(max_length=100), default=list)
    patient_id = models.CharField(max_length=100, null=True, blank=True)
    available = models.BooleanField(default=True, null=True, blank=True)

    def get_request(self):
        return Request.objects.filter(request_id=self.request_id, latest=True).first()

    def get_patient(self):
        return Patient.objects.filter(patient_id=self.patient_id, latest=True).first()

    def get_samples(self):
        return Sample.objects.filter(sample_id__in=self.samples, latest=True).all()

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


class FileMetadataManager(models.Manager):
    def _update_request(self, metadata):
        return Request.objects.create_or_update_instance(
            **RequestModelManager.extract_from_metadata(metadata), from_file=True
        )

    def _update_sample(self, metadata):
        return Sample.objects.create_or_update_instance(
            **SampleModelManager.extract_from_metadata(metadata), from_file=True
        )

    def _update_patient(self, metadata):
        return Patient.objects.create_or_update_instance(
            **PatientModelManager.extract_from_metadata(metadata), from_file=True
        )

    def _update_versioned_instance(self, updates, from_file=True):
        try:
            with transaction.atomic():
                file_id = updates.pop("file")
                objs = FileMetadata.objects.select_for_update().filter(file_id=file_id).order_by("-version").all()
                obj = objs.first()
                latest_metadata = obj.metadata
                updated_metadata = copy.deepcopy(latest_metadata)
                updated_metadata.update(updates["metadata"])
                diff = DeepDiff(updated_metadata, latest_metadata, ignore_order=True)
                if diff:
                    version = obj.version + 1
                    obj.latest = False
                    obj.save()
                    new_file_metadata = FileMetadata.objects.create(
                        file=obj.file, metadata=updated_metadata, user=updates["user"], version=version
                    )
                    updated_keys = [
                        key.replace("root['", "").replace("']", "") for key in diff.get("values_changed", {}).keys()
                    ]
                    file_obj_changed = False
                    if settings.REQUEST_ID_METADATA_KEY in updated_keys:
                        new_file_metadata.file.request_id = updated_metadata[settings.REQUEST_ID_METADATA_KEY]
                        file_obj_changed = True
                    if settings.SAMPLE_ID_METADATA_KEY in updated_keys:
                        new_file_metadata.file.samples = [updated_metadata[settings.SAMPLE_ID_METADATA_KEY]]
                        file_obj_changed = True
                    if settings.PATIENT_ID_METADATA_KEY in updated_keys:
                        new_file_metadata.file.patient_id = updated_metadata[settings.PATIENT_ID_METADATA_KEY]
                        file_obj_changed = True
                    if file_obj_changed:
                        new_file_metadata.file.save()
                    if from_file:
                        if settings.REQUEST_ID_METADATA_KEY in updated_keys:
                            self._update_request(updated_metadata)
                        if settings.SAMPLE_ID_METADATA_KEY in updated_keys:
                            self._update_sample(updated_metadata)
                        if settings.PATIENT_ID_METADATA_KEY in updated_keys:
                            self._update_patient(updated_metadata)
                    logger.debug(f"File {file_id} updated {str(new_file_metadata)}")
                    return new_file_metadata
                else:
                    logger.debug(f"No updates {str(obj)}")
                    return obj
        except IntegrityError as e:
            logger.debug(f"Integrity error {e}")
            return self._update_versioned_instance(updates, from_file)

    def create_or_update(self, from_file=True, **fields):
        current = locals()["fields"]
        logger.debug(current)
        obj, created = FileMetadata.objects.get_or_create(file=current["file"], latest=True, defaults=current)
        if created:
            if obj.metadata.get(settings.REQUEST_ID_METADATA_KEY):
                Request.objects.create_or_update_instance(
                    **RequestModelManager.extract_from_metadata(obj.metadata), from_file=from_file
                )
            if obj.metadata.get(settings.SAMPLE_ID_METADATA_KEY):
                Sample.objects.create_or_update_instance(
                    **SampleModelManager.extract_from_metadata(obj.metadata), from_file=from_file
                )
            if obj.metadata.get(settings.PATIENT_ID_METADATA_KEY):
                Patient.objects.create_or_update_instance(
                    **PatientModelManager.extract_from_metadata(obj.metadata), from_file=from_file
                )
            return obj
        else:
            return self._update_versioned_instance(current, from_file)


class FileMetadata(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    version = models.IntegerField(default=0)
    latest = models.BooleanField(default=True)
    metadata = JSONField(default=dict)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    objects = FileMetadataManager()

    def __str__(self):
        return f"{self.id} {self.version} {self.latest} {self.user}"

    class Meta:
        unique_together = ("file", "version")
        indexes = [
            models.Index(
                fields=["latest"],
                name="latest_idx",
            ),
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


class LowercaseCharField(models.CharField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return value if value is None else value.lower()


class MachineRunMode(BaseModel):
    machine_name = LowercaseCharField(max_length=32, null=False, blank=False, unique=True)
    machine_class = LowercaseCharField(max_length=32, null=False, blank=False)
    machine_type = models.CharField(max_length=32, null=False, blank=False)

    def __repr__(self):
        return "MACHINE: %s; CLASS: %s; TYPE: %s" % (self.machine_name, self.machine_class, self.machine_type)

    def __str__(self):
        return "{}".format(self.machine_name)


class PooledNormal(BaseModel):
    machine = LowercaseCharField(max_length=32, null=False, blank=False)
    bait_set = LowercaseCharField(max_length=32, null=False, blank=False)
    gene_panel = models.CharField(max_length=32, null=False, blank=False)
    preservation_type = models.CharField(max_length=32, null=False, blank=False)
    run_date = models.DateTimeField()
    pooled_normals_paths = ArrayField(models.CharField(max_length=255), blank=True, default=list)

    @property
    def formatted_run_date(self):
        return self.run_date.strftime("%m-%d-%Y")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["machine", "bait_set", "preservation_type"], name="unique_three_fields")
        ]

    def __repr__(self):
        return "MACHINE: %s; GENE_PANEL: %s; BAIT_SET: %s" % (self.machine, self.gene_panel, self.bait_set)

    def __str__(self):
        return "{}".format(self.machine)

    def save(self, *args, **kwargs):
        from .serializers import CreateFileSerializer

        for pooled_normal_path in self.pooled_normals_paths:
            if File.objects.filter(path=pooled_normal_path).exists():
                continue
            else:
                metadata = {
                    "machine": self.machine,
                    "genePanel": self.gene_panel,
                    "baitSet": self.bait_set,
                    "preservation": self.preservation_type,
                    "runDate": datetime.strftime(self.run_date, "%m-%d-%Y"),
                }
                data = {
                    "path": pooled_normal_path,
                    "metadata": metadata,
                    "file_type": "fastq",
                    "file_group": settings.POOLED_NORMAL_FILE_GROUP,
                }
                serializer = CreateFileSerializer(data=data)

                if not serializer.is_valid():
                    error_details = "; ".join([f"{field}: {error}" for field, error in serializer.errors.items()])
                    raise ValidationError(f"File creation failed with the following errors: {error_details}")
                else:
                    serializer.save()
        super().save(*args, **kwargs)
