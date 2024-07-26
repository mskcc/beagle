import logging
import os.path
from time import sleep
from django.apps import apps
from celery import shared_task
from django.conf import settings
from notifier.models import JobGroupNotifier


logger = logging.getLogger(__name__)


@shared_task
def populate_job_group_notifier_metadata(request_id, pi, investigator, assay):
    job_group_notifiers = JobGroupNotifier.objects.filter(
        request_id=request_id, PI__isnull=True, investigator__isnull=True, assay__isnull=True
    )
    for job_group_notifier in job_group_notifiers:
        logger.info(
            "Updating JobGroup {jg_id} with metadata requestId: {request_id} PI: {pi}, investigator: {investigator}, assay: {assay}".format(
                jg_id=str(job_group_notifier.id), request_id=request_id, pi=pi, investigator=investigator, assay=assay
            )
        )
        job_group_notifier.PI = pi
        job_group_notifier.investigator = investigator
        job_group_notifier.assay = assay
        job_group_notifier.save()


@shared_task
def check_for_missing_files():
    file_groups = settings.CHECK_FILE_GROUPS
    File = apps.get_model(app_label="file_system", model_name="File")
    # Check for missing files
    for fg in file_groups:
        files = File.objects.filter(file_group=fg).all()
        for f in files:
            if not os.path.exists(path=f.path):
                f.set_missing()
            else:
                if f.missing:
                    f.set_not_missing()
            sleep(5)
    generate_report_of_missing_files.delay()


@shared_task()
def generate_report_of_missing_files():
    file_groups = settings.CHECK_FILE_GROUPS
    File = apps.get_model(app_label="file_system", model_name="File")
    for fg in file_groups:
        files = File.objects.filter(file_group=fg, missing=True).all()
