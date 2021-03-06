import os
import uuid
from enum import IntEnum
from django.db import models
from django.conf import settings
from django.db import transaction
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GinIndex


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


class Sample(BaseModel):
    sample_id = models.CharField(max_length=32, unique=True, null=False, blank=False)
    redact = models.BooleanField(default=False, null=False)


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
    sample = models.ForeignKey(Sample, null=True, on_delete=models.SET_NULL)

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
        sample_id = self.metadata.get(settings.SAMPLE_ID_METADATA_KEY)
        if sample_id:
            with transaction.atomic():
                try:
                    sample = Sample.objects.get(sample_id=sample_id)
                except Sample.DoesNotExist:
                    sample = Sample.objects.create(sample_id=sample_id)
                self.file.sample = sample
                self.file.save(update_fields=('sample',))
        if do_not_version:
            super(FileMetadata, self).save(*args, **kwargs)
        else:
            versions = FileMetadata.objects.filter(file_id=self.file.id).values_list('version', flat=True)
            version = max(versions) + 1 if versions else 0
            self.version = version
            self.latest = True
            old = FileMetadata.objects.filter(file_id=self.file.id).order_by('-created_date').first()
            if old:
                old.latest = False
                old.save(do_not_version=True)
            super(FileMetadata, self).save(*args, **kwargs)

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


class FileRunMap(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    run = JSONField(default=list)

