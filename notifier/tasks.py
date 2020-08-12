import logging
from celery import shared_task
from django.conf import settings
from notifier.models import JobGroupNotifier, Notifier
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler


logger = logging.getLogger(__name__)


def event_handler(job_group_notifier):
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier)
        if jgn.notifier_type.notifier_type == "JIRA":
            logger.info("Notifier type JIRA created")
            return JiraEventHandler(jgn.notifier_type.board)
        else:
            return NoOpEventHandler()
    except JobGroupNotifier.DoesNotExist:
        raise Exception("This shouldn't happen")


def notifier_start(job_group, request_id, operator=None):
    if settings.NOTIFIER_ACTIVE:
        try:
            notifier = Notifier.objects.get(operator_id=operator)
        except Notifier.DoesNotExist:
            notifier = Notifier.objects.get(default=True)
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group,
                                                             notifier_type=notifier)
        eh = event_handler(job_group_notifier.id)
        notifier_id = eh.start(request_id)
        job_group_notifier.jira_id = notifier_id
        job_group_notifier.save()
        return str(job_group_notifier.id)
    logger.info("Notifier Inactive")
    return None


@shared_task
def send_notification(event):
    if settings.NOTIFIER_ACTIVE:
        logger.info(event)
        eh = event_handler(event['job_notifier'])
        eh.process(event)
    else:
        logger.info("Notifier Inactive")

