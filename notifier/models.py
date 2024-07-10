import uuid
from enum import IntEnum
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class Notifier(BaseModel):
    default = models.BooleanField(default=False)
    notifier_type = models.CharField(max_length=100, null=False)
    board = models.CharField(max_length=20, null=False)


class JobGroup(BaseModel):
    @property
    def timestamp(self):
        return self.created_date.strftime("%Y%m%d_%H%M")


class JiraStatus(IntEnum):
    UNKNOWN = 0
    NOT_FOR_CI = 1
    CANT_DO = 2
    TERMINAL_DELIVER_AS_IS = 3
    PARTIAL_DELIVERY_WILL_RERUN_REMAINING = 4
    DELIVER_AS_IS_WILL_NOT_RERUN = 5
    NO_DELIVERY_WILL_REEXECUTE = 6
    PRIMARY_OUTPUT_DELIVERY = 7
    DONE = 8
    CI_REVIEW_NEEDED = 9
    INCOMPLETE_REQUEST = 10
    PM_HOLD = 11
    MISSING_INFORMATION = 12
    SOMEDAY_MAYBE = 13
    PIPELINE_COMPLETED_NO_FAILURES = 14
    WAITING_FOR_PORTAL = 15
    READY_FOR_STANDARD_DELIVERY = 16
    READY_FOR_CUSTOM_DELIVERY = 17
    IN_VOYAGER = 18
    ADMIN_HOLD = 19
    IMPORT_COMPLETE = 20
    IMPORT_PARTIALLY_COMPLETE = 21


class JobGroupNotifier(BaseModel):
    jira_id = models.CharField(max_length=20, blank=True, null=True)
    request_id = models.CharField(max_length=100, blank=True, null=True)
    job_group = models.ForeignKey(JobGroup, null=False, blank=False, on_delete=models.CASCADE)
    notifier_type = models.ForeignKey(Notifier, null=False, blank=False, on_delete=models.CASCADE)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in JiraStatus], default=JiraStatus.UNKNOWN
    )
    investigator = models.CharField(max_length=40, blank=True, null=True)
    PI = models.CharField(max_length=40, blank=True, null=True)
    assay = models.CharField(max_length=30, blank=True, null=True)
