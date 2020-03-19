import logging
from celery import shared_task
from django.conf import settings
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler


logger = logging.getLogger(__name__)


def event_handler():
    if settings.NOTIFIER == "JIRA":
        return JiraEventHandler()
    else:
        return NoOpEventHandler()


@shared_task
def send_notification(event):
    event_handler().process(event)
