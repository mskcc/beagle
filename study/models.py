import uuid
from django.db import models
from file_system.models import Request, Sample


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class Study(models.Model):
    study_id = models.CharField(max_length=40, null=False)
    requests = models.ManyToManyField(Request)
    samples = models.ManyToManyField(Sample)
    
