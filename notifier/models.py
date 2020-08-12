import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class Notifier(BaseModel):
    default = models.BooleanField(default=False)
    notifier_type = models.CharField(max_length=100, null=False)
    board = models.CharField(max_length=20, null=False)
    operator = models.ForeignKey('beagle_etl.Operator', null=True, blank=True, on_delete=models.CASCADE)


class JobGroup(BaseModel):
    jira_id = models.CharField(max_length=20, blank=True, null=True)

    @property
    def timestamp(self):
        return self.created_date.strftime('%Y%m%d_%H%M')


class JobGroupNotifier(BaseModel):
    jira_id = models.CharField(max_length=20, blank=True, null=True)
    job_group = models.ForeignKey(JobGroup, null=False, blank=False, on_delete=models.CASCADE)
    notifier_type = models.ForeignKey(Notifier, null=False, blank=False, on_delete=models.CASCADE)


