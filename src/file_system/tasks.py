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


@shared_task
def check_fastq_files():
    File = apps.get_model(app_label="file_system", model_name="File")
    files = File.objects.filter(file_group=settings.IMPORT_FILE_GROUP)
    current_date = datetime.now().strftime("%m_%d_%Y")
    file_name = f"missing_files_report_{current_date}.txt"
    report_file = open(os.path.join(settings.MISSING_FILES_REPORT_PATH, file_name), "w")
    for f in files:
        if not os.path.exists(f.path):
            f.available = False
            f.save()
            report_file.write(f"{f.path}\n")
        else:
            if not f.available:
                f.available = True
                f.save()
    report_file.close()
    remove_oldest_file(settings.MISSING_FILES_REPORT_PATH)


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
