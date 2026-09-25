import os
import logging
from datetime import datetime
from celery import shared_task
from django.apps import apps
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


def remove_oldest_file(directory):
    oldest_date = None
    oldest_file = None
    count = 0
    for filename in os.listdir(directory):
        if filename.startswith("missing_files_report_") and filename.endswith(".txt"):
            count += 1
            date_str = filename[len("missing_files_report_") : -len(".txt")]
            file_date = datetime.strptime(date_str, "%m_%d_%Y")
            if oldest_date is None or file_date < oldest_date:
                oldest_date = file_date
                oldest_file = filename
    if count > settings.MISSING_FILES_REPORT_COUNT and oldest_file:
        os.remove(os.path.join(directory, oldest_file))
