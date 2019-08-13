import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Pipeline(BaseModel):
    name = models.CharField(max_length=100, editable=True)
    github = models.CharField(max_length=300, editable=True)
    version = models.CharField(max_length=100, editable=True)
    entrypoint = models.CharField(max_length=100, editable=True)


class Run(BaseModel):
    app = JSONField()
    inputs = JSONField()
    outputs = JSONField()
