import os
import uuid
from enum import IntEnum
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify


class StorageType(IntEnum):
    LOCAL = 0
    AWS_S3 = 1


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Storage(BaseModel):
    name = models.CharField(max_length=20)
    type = models.IntegerField(choices=[(storage_type.value, storage_type.name) for storage_type in StorageType])

    def __repr__(self):
        return "ID: %s NAME: %s TYPE: %s" % (self.id, self.name, StorageType(self.type))


class Sample(BaseModel):
    sample_name = models.CharField(max_length=40, editable=True)
    metadata = JSONField(default=dict)


class Cohort(BaseModel):
    name = models.CharField(max_length=40, editable=True)
    slug = models.SlugField(unique=True)
    storage = models.ForeignKey(Storage, blank=True, null=True, on_delete=models.SET_NULL)
    metadata = JSONField(default=dict)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Cohort, self).save(*args, **kwargs)


class CohortMetadata(BaseModel):
    cohort = models.ForeignKey(Cohort, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict)


class File(BaseModel):
    file_name = models.CharField(max_length=100)
    path = models.CharField(max_length=400)
    size = models.BigIntegerField()
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, blank=True, null=True, on_delete=models.SET_NULL)
    version = models.IntegerField()


class FileMetadata(BaseModel):
    file = models.ForeignKey(File, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict)

    def save(self, *args, **kwargs):
        versions = FileMetadata.objects.filter(file_id=self.file.id).values_list('version', flat=True)
        version = max(versions) + 1 if versions else 0
        self.version = version
        self.file.version = versions
        self.file.save()
        super(FileMetadata, self).save(*args, **kwargs)

