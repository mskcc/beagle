import logging
from celery import shared_task
from django.conf import settings
from notifier.models import JobGroup
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler
from notifier.event_handler.seqosystem_event_handler.seqosystem_event_handler import SeqosystemEventHandler


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
    elif handler_type == "SEQO":
        logger.info("Notifier type SEQO created")
        return SeqosystemEventHandler()
    else:
        return NoOpEventHandler()


def notifier_start(request_id):
    attrs = {}
    for eh in event_handlers():
        if eh.db_name:
            try:
                notifier_id = eh.start(request_id)
                attrs[eh.db_name] = notifier_id
            except Exception:
                logging.error("Failed to start notifier for event_handler %s", str(event_handler))

    job_group = JobGroup(**attrs)
    job_group.save()
    return job_group

@shared_task
def send_notification(event):
    for event_handler in event_handlers():
        event_handler.process(event)
