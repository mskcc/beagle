import shutil
import logging
from celery import shared_task
from django.conf import settings
from datetime import date, datetime, timedelta
from copy_service.copy_service import CopyService
from .models import FileProviderStatus, FileProviderJob, SampleProviderJob, CleanupFileJob


logger = logging.getLogger()


@shared_task
def stage_file_job(file_provide_job_id, sample_job=None):
    file_provide_job = FileProviderJob.objects.get(id=file_provide_job_id)
    file_provide_job.in_progress()

    CopyService.copy(file_provide_job.original_path, file_provide_job.staged_path)
    file_provide_job.file_object.path = file_provide_job.staged_path
    file_provide_job.file_object.set_available()

    file_provide_job.set_completed()

    if sample_job:
        try:
            sample_job = SampleProviderJob.objects.get(id=sample_job)
            sample_job.increment_completed()
        except SampleProviderJob.DoesNotExist:
            logger.warning(f"SampleProviderJob for id {sample_job} not found")

    clean_up_date = date.today() + timedelta(days=settings.STAGE_DAYS)
    CleanupFileJob.objects.create(file_object=file_provide_job.file_object,
                                  original_path=file_provide_job.original_path,
                                  cleanup_date=clean_up_date)


@shared_task
def check_for_clean_up():
    clean_up_jobs = CleanupFileJob.objects.filter(cleanup_dat=date.today())
    for job in clean_up_jobs:
        clean_up_file.delay(str(job.id))


@shared_task
def clean_up_file(clean_up_file_job_id):
    try:
        clean_up_file_job = CleanupFileJob.objects.get(id=clean_up_file_job_id)
    except CleanupFileJob.DoesNotExist:
        logger.error(f"CleanupFileJob with id {clean_up_file_job_id} doesn't exist")
        return
    try:
        shutil.rmtree(clean_up_file_job.file_object.file.path)
    except Exception as e:
        logger.error(f"Failed to delete file {clean_up_file_job.file_object.file.path}. {str(e)}")
    else:
        clean_up_file_job.file_object.path = clean_up_file_job.original_path
        clean_up_file_job.file_object.file.set_unavailable()
        clean_up_file_job.set_completed()