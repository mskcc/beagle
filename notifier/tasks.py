import logging
from celery import shared_task
from django.conf import settings
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler


logger = logging.getLogger(__name__)


def event_handlers():
    result = []
    for n in settings.NOTIFIERS:
        result.append(event_handler(n))
    return result


def event_handler(handler_type):
    if handler_type == "JIRA":
        logger.info("Notifier type JIRA created")
        return JiraEventHandler()
    else:
        return NoOpEventHandler()


def notifier_start(job_group, request_id):
    for eh in event_handlers():
        notifier_id = eh.start(request_id)
        try:
            setattr(job_group, eh.db_name, notifier_id)
            job_group.save()
        except Exception:
            logging.error("Failed to start notifier for event_handler %s", str(event_handler))


@shared_task
def send_notification(event):
    for event_handler in event_handlers():
        event_handler.process(event)
