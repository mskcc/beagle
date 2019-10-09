from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

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


app.conf.beat_schedule = {
    "fetch_requests_from_lims": {
        "task": "beagle_etl.tasks.fetch_requests_lims",
        "schedule": 900.0
    },
    "scheduler_tick": {
        "task": "beagle_etl.tasks.scheduler",
        "schedule": 15.0
    }
}
