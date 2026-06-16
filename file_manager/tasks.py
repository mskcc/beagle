import os
import logging
from celery import shared_task
from django.conf import settings
from datetime import date, datetime, timedelta
from file_manager.copy_service.copy_service import CopyService
from .models import FileProviderStatus, FileProviderJob, SampleProviderJob, CleanupFileJob


logger = logging.getLogger()


@shared_task
def stage_file_job(file_provide_job_id, sample_job=None):
    file_provide_job = FileProviderJob.objects.get(id=file_provide_job_id)
    file_provide_job.in_progress()

    try:
        CopyService.copy(file_provide_job.original_path, file_provide_job.staged_path)
        file_provide_job.file_object.path = file_provide_job.staged_path
        file_provide_job.file_object.set_available()
    except Exception as e:
        logger.error(f"Failed to copy file {str(e)}")
        file_provide_job.set_failed()
    else:
        file_provide_job.set_completed()
        if sample_job:
            try:
                sample_job = SampleProviderJob.objects.get(id=sample_job)
                sample_job.increment_completed()
            except SampleProviderJob.DoesNotExist:
                logger.warning(f"SampleProviderJob for id {sample_job} not found")

        clean_up_date = date.today() + timedelta(days=settings.STAGE_DAYS)
        CleanupFileJob.objects.create(
            file_object=file_provide_job.file_object,
            original_path=file_provide_job.original_path,
            cleanup_date=clean_up_date,
        )


@shared_task
def stage_samples_job(sample_ids, file_group=None):
    """
    Stage files for a list of samples in the background.

    For each sample, creates the SampleProviderJob and FileProviderJob records
    and dispatches a stage_file_job task per file that needs staging.
    """
    from file_manager.file_manager.file_manager import FileManager

    if file_group is None:
        file_group = settings.IMPORT_FILE_GROUP

    file_manager = FileManager(file_group=file_group)

    for sample_id in sample_ids:
        try:
            sample_job, task_sigs = file_manager.stage_sample(sample_id)
        except Exception as e:
            logger.error(f"Error staging sample {sample_id}: {str(e)}")
            continue

        if sample_job.total_files > 0:
            if task_sigs:
                for task in task_sigs:
                    task.delay()
                logger.info(f"Staged {len(task_sigs)} files for sample {sample_id}")
            else:
                logger.warning(
                    f"Sample {sample_id} has {sample_job.total_files} files to stage, "
                    f"but no tasks were created (files may already be staging)"
                )
        else:
            logger.info(f"No files need staging for sample {sample_id}")


@shared_task
def check_for_clean_up():
    clean_up_jobs = CleanupFileJob.objects.filter(cleanup_date=date.today())
    for job in clean_up_jobs:
        clean_up_file.delay(str(job.id))


@shared_task
def clean_up_file(clean_up_file_job_id):
    try:
        clean_up_file_job = CleanupFileJob.objects.get(id=clean_up_file_job_id)
    except CleanupFileJob.DoesNotExist:
        logger.error(f"CleanupFileJob with id {clean_up_file_job_id} doesn't exist")
        return

    file_path = clean_up_file_job.file_object.path
    try:
        if file_path == clean_up_file_job.original_path:
            logger.error(f"File is not staged {file_path}. Skip cleanup to avoid deleting original file!")
            return
        elif os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Successfully deleted file {file_path}")
        else:
            logger.warning(f"File {file_path} does not exist, skipping deletion")
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}. {str(e)}")
        return

    clean_up_file_job.file_object.path = clean_up_file_job.original_path
    clean_up_file_job.file_object.set_unavailable()
    clean_up_file_job.set_completed()
