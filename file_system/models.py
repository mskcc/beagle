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


class FileType(models.Model):
    ext = models.CharField(max_length=20)


class FileGroup(BaseModel):
    name = models.CharField(max_length=40, editable=True)
    slug = models.SlugField(unique=True)
    storage = models.ForeignKey(Storage, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(FileGroup, self).save(*args, **kwargs)


class FileGroupMetadata(BaseModel):
    file_group = models.ForeignKey(FileGroup, blank=False, null=False, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict, blank=True, null=True)


class File(BaseModel):
    file_name = models.CharField(max_length=500)
    path = models.CharField(max_length=1500)
    file_type = models.ForeignKey(FileType, null=True, on_delete=models.SET_NULL)
    size = models.BigIntegerField()
    file_group = models.ForeignKey(FileGroup, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.size:
            try:
                self.size = os.path.getsize(self.path)
            except Exception:
                self.size = 0
        super(File, self).save(*args, **kwargs)


class FileMetadata(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    version = models.IntegerField()
    metadata = JSONField(default=dict)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        versions = FileMetadata.objects.filter(file_id=self.file.id).values_list('version', flat=True)
        version = max(versions) + 1 if versions else 0
        self.version = version
        super(FileMetadata, self).save(*args, **kwargs)


class FileRunMap(BaseModel):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    run = JSONField(default=list)

