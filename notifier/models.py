import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class JobGroup(BaseModel):
    jira_id = models.CharField(max_length=20, blank=True, null=True)

    @property
    def timestamp(self):
        return self.created_date.strftime('%Y%m%d_%H%M')
