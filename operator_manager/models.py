import uuid
import logging
from enum import IntEnum
from django.db import models
from django.db.models import JSONField
from django.utils.timezone import now
from notifier.models import Notifier
from beagle_etl.models import JobGroup, JobGroupNotifier
from runner.models import BaseModel, RunStatus, TriggerRunType, TriggerAggregateConditionType


logger = logging.getLogger()


class OperatorVersion(IntEnum):
    V1 = 0  # Legacy Operators
    V2 = 1


class OperatorStatus(IntEnum):
    INSTALLING = 0
    READY = 1
    FAILED = 2


class Operator(models.Model):
    name = models.CharField(max_length=100, default=False)
    type = models.IntegerField(
        choices=[(status.value, status.name) for status in OperatorVersion],
        db_index=True,
    )

    class_name = models.CharField(max_length=150)
    version = models.CharField(max_length=50, null=True, blank=True)

    github_url = models.CharField(max_length=200, null=True, blank=True)

    docker_image_tag = models.CharField(max_length=200, null=True, blank=True)
    docker_image_id = models.CharField(max_length=100, null=True, blank=True)

    status = models.IntegerField(
        choices=[(status.value, status.name) for status in OperatorStatus],
        default=OperatorStatus.INSTALLING,
        db_index=True,
    )

    trigger = JSONField(default=list, null=True)

    notifier = models.ForeignKey(
        Notifier, null=True, blank=True, on_delete=models.CASCADE, related_name="sdk_operators"
    )

    active = models.BooleanField(default=False)

    @property
    def is_installing(self):
        return self.status == OperatorStatus.INSTALLING

    @property
    def is_active(self):
        return self.active

    def ready(self, docker_image_tag, docker_image_id):
        self.docker_image_tag = docker_image_tag
        self.docker_image_id = docker_image_id
        self.status = OperatorStatus.READY
        self.save(update_fields=["docker_image_tag", "docker_image_id", "status"])

    def __str__(self):
        return "{}".format(self.name)


class OperatorTrigger(BaseModel):
    from_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="from_triggers")
    to_operator = models.ForeignKey(Operator, null=True, on_delete=models.SET_NULL, related_name="to_triggers")
    aggregate_condition = models.IntegerField(
        choices=[(t.value, t.name) for t in TriggerAggregateConditionType], null=True
    )
    run_type = models.IntegerField(choices=[(t.value, t.name) for t in TriggerRunType])

    def __str__(self):
        if self.run_type == TriggerRunType.AGGREGATE:
            return "{} -> {} when {}".format(
                self.from_operator,
                self.to_operator,
                TriggerAggregateConditionType(self.aggregate_condition).name.title(),
            )
        elif self.run_type == TriggerRunType.INDIVIDUAL:
            return "{} -> {} on each run".format(self.from_operator, self.to_operator)
        else:
            return "{} -> {}".format(self.from_operator, self.to_operator)


class OperatorRun(BaseModel):
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in RunStatus], default=RunStatus.CREATING, db_index=True
    )
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    num_total_runs = models.IntegerField(null=False)
    num_manual_restarts = models.IntegerField(null=False, default=0)
    triggered_alert = models.BooleanField(default=False)
    num_completed_runs = models.IntegerField(null=False, default=0)
    num_failed_runs = models.IntegerField(null=False, default=0)
    job_group = models.ForeignKey(JobGroup, null=True, blank=True, on_delete=models.SET_NULL)
    job_group_notifier = models.ForeignKey(JobGroupNotifier, null=True, blank=True, on_delete=models.SET_NULL)
    finished_date = models.DateTimeField(blank=True, null=True, db_index=True)
    parent = models.ForeignKey("self", default=None, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        if self.status == RunStatus.COMPLETED or self.status == RunStatus.FAILED:
            if not self.finished_date:
                self.finished_date = now()
        super().save(*args, **kwargs)

    def complete(self):
        self.status = RunStatus.COMPLETED
        self.save()

    def fail(self):
        self.status = RunStatus.FAILED
        self.save()

    def increment_failed_run(self):
        self.refresh_from_db()
        self.num_failed_runs += 1
        self.save()

    def increment_completed_run(self):
        self.refresh_from_db()
        self.num_completed_runs += 1
        self.save()

    def increment_manual_restart(self):
        self.refresh_from_db()
        self.num_manual_restarts += 1
        self.save()

    @property
    def percent_runs_succeeded(self):
        if self.num_completed_runs >= self.num_total_runs:
            return float(100)
        if self.num_total_runs > 0:
            return float("{0:.2f}".format(self.num_completed_runs / self.num_total_runs * 100.0))
        else:
            return float(0)

    @property
    def percent_runs_finished(self):
        if self.num_total_runs > 0:
            return float(
                "{0:.2f}".format((self.num_failed_runs + self.num_completed_runs) / self.num_total_runs * 100.0)
            )
        else:
            return 0

    @property
    def total_runs(self):
        self.refresh_from_db()
        return self.num_total_runs

    @property
    def completed_runs(self):
        self.refresh_from_db()
        return self.num_completed_runs

    @property
    def failed_runs(self):
        self.refresh_from_db()
        return self.num_failed_runs

    @property
    def running_runs(self):
        self.refresh_from_db()
        return self.num_total_runs - (self.num_completed_runs + self.num_failed_runs)

    @property
    def operator_finished(self):
        self.refresh_from_db()
        return (self.num_failed_runs + self.num_completed_runs) == self.num_total_runs
