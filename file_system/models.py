import os
import uuid
from enum import IntEnum
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User


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
    name = models.CharField(max_length=40, editable=True)
    tags = JSONField(default=dict)


class SampleMetadata(BaseModel):
    sample = models.ForeignKey(Sample, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        versions = SampleMetadata.objects.filter(sample_id=self.sample.id).values_list('version', flat=True)
        version = max(versions) + 1 if versions else 0
        self.version = version
        self.sample.save()
        super(SampleMetadata, self).save(*args, **kwargs)


class FileGroup(BaseModel):
    name = models.CharField(max_length=40, editable=True)
    slug = models.SlugField(unique=True)
    storage = models.ForeignKey(Storage, blank=True, null=True, on_delete=models.SET_NULL)
    metadata = JSONField(default=dict, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FileGroup, self).save(*args, **kwargs)


class FileGroupMetadata(BaseModel):
    cohort = models.ForeignKey(FileGroup, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict, blank=True, null=True)


class File(BaseModel):
    file_name = models.CharField(max_length=100)
    path = models.CharField(max_length=400)
    size = models.BigIntegerField()
    lane = models.IntegerField()
    pair_end = models.IntegerField()
    file_group = models.ForeignKey(FileGroup, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, blank=True, null=True, on_delete=models.CASCADE)
