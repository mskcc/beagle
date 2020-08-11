import logging
from celery import shared_task
from django.conf import settings
from notifier.models import JobGroupNotifier, Notifier
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler


logger = logging.getLogger(__name__)


# def event_handlers():
#     result = []
#     for n in settings.NOTIFIERS:
#         result.append(event_handler(n))
#     return result


# def event_handler(handler_type):
#     if handler_type == "JIRA":
#         logger.info("Notifier type JIRA created")
#         return JiraEventHandler()
#     else:
#         return NoOpEventHandler()


# def event_handler(job_group, notifier_type=None):
#     try:
#         jgn = JobGroupNotifier.objects.get(id=job_group, notifier_type=notifier_type)
#     except JobGroupNotifier.DoesNotExist:
#         jgn = JobGroupNotifier.objects.get(default=True)
#     return jgn


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


# def notifier_start(job_group, request_id):
#     for eh in event_handlers():
#         notifier_id = eh.start(request_id)
#         try:
#             setattr(job_group, eh.db_name, notifier_id)
#             job_group.save()
#         except Exception:
#             logging.error("Failed to start notifier for event_handler %s", str(event_handler))


@shared_task
def send_notification(event):
    logger.info(event)
    eh = event_handler(event['job_group'])
    eh.process(event)

