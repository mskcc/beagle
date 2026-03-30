from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger, worker_ready

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")

app = Celery("etl_job")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter("%(asctime)s|%(levelname)s|%(name)s|%(task_id)s|%(task_name)s|%(name)s|%(message)s")
        )


app.conf.task_routes = {
    "runner.tasks.process_triggers": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.create_run_task": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.terminate_job_task": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.submit_job": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.create_jobs_from_request": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.create_jobs_from_chaining": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.create_jobs_from_pairs": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.create_operator_run_from_jobs": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.add_pipeline_to_cache": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.running_job": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.terminate_job": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.complete_job": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "runner.tasks.fail_job": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    "notifier.tasks.send_notification": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "file_system.tasks.populate_job_group_notifier_metadata": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.tasks.job_processor": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.tasks.process_smile_events": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.tasks.process_job_with_lock": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.jobs.metadb_jobs.update_job": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.jobs.metadb_jobs.not_supported": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.jobs.metadb_jobs.request_callback": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "beagle_etl.jobs.metadb_jobs.calculate_checksum": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    "file_manager.tasks.stage_file_job": {"queue": settings.BEAGLE_FILE_MANAGER_QUEUE},
    "file_manager.tasks.check_for_clean_up": {"queue": settings.BEAGLE_FILE_MANAGER_QUEUE},
    "file_manager.tasks.clean_up_file": {"queue": settings.BEAGLE_FILE_MANAGER_QUEUE},
}

app.conf.beat_schedule = {
    "process_request_callback_jobs": {
        "task": "beagle_etl.tasks.process_request_callback_jobs",
        "schedule": settings.PROCESS_REQUEST_CALLBACK_PERIOD,
        "options": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    },
    "process_smile_imports": {
        "task": "beagle_etl.tasks.process_smile_events",
        "schedule": settings.PROCESS_SMILE_MESSAGES_PERIOD,
        "options": {"queue": settings.BEAGLE_DEFAULT_QUEUE},
    },
    "check_status": {
        "task": "runner.tasks.check_jobs_status",
        "schedule": settings.CHECK_JOB_STATUS_PERIOD,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    },
    "check_operator_run_alerts": {
        "task": "runner.tasks.check_operator_run_alerts",
        "schedule": crontab(minute=0, hour=0),
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    },
    "process_triggers": {
        "task": "runner.tasks.process_triggers",
        "schedule": settings.PROCESS_TRIGGERS_PERIOD,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    },
    "timeout_runs": {
        "task": "runner.tasks.check_job_timeouts",
        "schedule": settings.CHECK_JOB_TIMEOUTS,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    },
    "check_job_group_watcher": {
        "task": "study.tasks.check_job_group_watcher",
        "schedule": settings.CHECK_JOB_TIMEOUTS,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE},
    },
    "check_staged_file_cleanup": {
        "task": "file_manager.tasks.check_for_clean_up",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": settings.BEAGLE_FILE_MANAGER_QUEUE},
    },
}
