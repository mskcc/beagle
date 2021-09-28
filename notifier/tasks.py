import logging
from celery import shared_task
from django.conf import settings
from file_system.repository import FileRepository
from notifier.models import JobGroupNotifier, Notifier
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


def notifier_start(job_group, request_id, operator=None):
    if settings.NOTIFIER_ACTIVE:
        notifier = Notifier.objects.get(default=True)
        try:
            if operator:
                notifier = Notifier.objects.filter(operator__id=operator.id).first()
        except Notifier.DoesNotExist:
            pass
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group,
                                                             request_id=request_id,
                                                             notifier_type=notifier)
        eh = event_handler(job_group_notifier.id)
        notifier_id = eh.start(request_id)
        job_group_notifier.jira_id = notifier_id
        if notifier_id.startswith(settings.JIRA_PREFIX):
            file_obj = FileRepository.filter(metadata={'requestId': request_id}).first()
            job_group_notifier.PI = file_obj.metadata.get('labHeadName')
            job_group_notifier.investigator = file_obj.metadata.get('investigatorName')
            job_group_notifier.assay = file_obj.metadata.get('recipe')
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


@shared_task
def populate_job_group_notifier_metadata(request_id, pi, investigator, assay):
    job_group_notifiers = JobGroupNotifier.objects.filter(request_id=request_id,
                                                          PI__isnull=True,
                                                          investigator__isnull=True,
                                                          assay__isnull=True)
    for job_group_notifier in job_group_notifiers:
        logger.info(
            "Updating JobGroup {jg_id} with metadata requestId: {request_id} PI: {pi}, investigator: {investigator}, assay: {assay}".format(
                jg_id=str(job_group_notifier.id),
                request_id=request_id,
                pi=pi,
                investigator=investigator,
                assay=assay))
        job_group_notifier.PI = pi
        job_group_notifier.investigator = investigator
        job_group_notifier.assay = assay
        job_group_notifier.save()
