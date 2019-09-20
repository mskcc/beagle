from __future__ import absolute_import, unicode_literals
import os
from .tasks import fetch_requests_lims
from celery import Celery, Task
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beagle.settings')

app = Celery('etl_job')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='LIMS_ETL')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls test('hello') every 10 seconds.
#     sender.add_periodic_task(10.0, fetch_requests_lims.s('hello'), name='add every 10')



    # Executes every Monday morning at 7:30 a.m.
    # sender.add_periodic_task(
    #     crontab(hour=7, minute=30, day_of_week=1),
    #     test.s('Happy Mondays!'),
    # )

app.conf.beat_schedule = {
    "fetch_requests_from_lims": {
        "task": "file_system.tasks.fetch_requests_lims",
        "schedule": 10.0
    }
}