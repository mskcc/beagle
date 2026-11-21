import uuid
import logging
from enum import IntEnum
from django.db import models
from django.db.models import JSONField
from notifier.models import Notifier


logger = logging.getLogger()



class OperatorVersion(IntEnum):
    V1 = 0 # Legacy Operators
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
        db_index=True
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


