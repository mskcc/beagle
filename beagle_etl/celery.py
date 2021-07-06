from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger, worker_ready

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beagle.settings')

app = Celery('etl_job')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter("%(asctime)s|%(levelname)s|%(name)s|%(task_id)s|%(task_name)s|%(name)s|%(message)s"))


@worker_ready.connect
def at_start(sender, **k):
    with sender.app.connection() as conn:
        print(conn)
        sender.app.send_task('beagle_etl.tasks.fetch_request_nats', connection=conn)


app.conf.task_routes = {
    'beagle_etl.tasks.scheduler': {'queue': settings.BEAGLE_JOB_SCHEDULER_QUEUE},
    'runner.tasks.process_triggers': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.create_run_task': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.abort_job_task': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.submit_job': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.create_jobs_from_request': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.create_jobs_from_chaining': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'runner.tasks.add_pipeline_to_cache': {'queue': settings.BEAGLE_RUNNER_QUEUE},
    'beagle_etl.tasks.fetch_requests_lims': {'queue': settings.BEAGLE_DEFAULT_QUEUE},
    'notifier.tasks.send_notification': {'queue': settings.BEAGLE_DEFAULT_QUEUE},
    'beagle_etl.tasks.job_processor': {'queue': settings.BEAGLE_DEFAULT_QUEUE},
    'beagle_etl.tasks.fetch_request_nats': {'queue': settings.BEAGLE_NATS_QUEUE}
}

app.conf.beat_schedule = {
    "scheduler_tick": {
        "task": "beagle_etl.tasks.scheduler",
        "schedule": 15.0,
        "options": {"queue": settings.BEAGLE_JOB_SCHEDULER_QUEUE}
    },
    'check_status': {
        "task": "runner.tasks.check_jobs_status",
        "schedule": 30.0,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE}
    },
    "process_triggers": {
        "task": "runner.tasks.process_triggers",
        "schedule": 120.0,
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE}
    },
    "timeout_runs": {
        "task": "runner.tasks.check_job_timeouts",
        "schedule": 86400.0, # 1 day
        "options": {"queue": settings.BEAGLE_RUNNER_QUEUE}
    },

}
