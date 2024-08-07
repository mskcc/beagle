import logging
from celery import shared_task
from django.conf import settings
from file_system.repository import FileRepository
from notifier.models import JobGroupNotifier, Notifier, JobGroup
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from notifier.event_handler.noop_event_handler.noop_event_handler import NoOpEventHandler
from notifier.event_handler.email_event_handler.email_event_handler import EmailEventHandler


logger = logging.getLogger(__name__)


def event_handler(job_group_notifier):
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier)
        if jgn.notifier_type.notifier_type == "JIRA":
            logger.info("Notifier type JIRA created")
            return JiraEventHandler(jgn.notifier_type.board)
        elif jgn.notifier_type.notifier_type == "EMAIL":
            logger.info("Notifier type EMAIL created")
            return EmailEventHandler()
        else:
            return NoOpEventHandler()
    except JobGroupNotifier.DoesNotExist:
        raise Exception("This shouldn't happen")


def notifier_start(job_group, request_id, operator=None, metadata={}):
    if settings.NOTIFIER_ACTIVE:
        notifier = Notifier.objects.get(default=True)
        try:
            if operator:
                operator_notifier = Notifier.objects.filter(operator__id=operator.id).first()
                if operator_notifier:
                    notifier = operator_notifier
        except Notifier.DoesNotExist:
            pass
        job_group_notifier = JobGroupNotifier.objects.create(
            job_group=job_group, request_id=request_id, notifier_type=notifier
        )
        eh = event_handler(job_group_notifier.id)
        notifier_id = eh.start(request_id)
        job_group_notifier.jira_id = notifier_id
        if notifier_id.startswith(settings.JIRA_PREFIX):
            file_obj = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id}).first()
            if file_obj:
                job_group_notifier.PI = file_obj.metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY, "")[:40]
                job_group_notifier.investigator = file_obj.metadata.get(settings.INVESTIGATOR_NAME_METADATA_KEY, "")[
                    :40
                ]
                job_group_notifier.assay = file_obj.metadata.get(settings.RECIPE_METADATA_KEY, "")
            else:
                job_group_notifier.PI = metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY, "")[:40]
                job_group_notifier.investigator = metadata.get(settings.INVESTIGATOR_NAME_METADATA_KEY, "")[:40]
                job_group_notifier.assay = metadata.get(settings.RECIPE_METADATA_KEY)
        job_group_notifier.save()
        return str(job_group_notifier.id)
    logger.info("Notifier Inactive")
    return None


@shared_task
def send_notification(event):
    if settings.NOTIFIER_ACTIVE:
        logger.info(event)
        eh = event_handler(event["job_notifier"])
        eh.process(event)
    else:
        logger.info("Notifier Inactive")
