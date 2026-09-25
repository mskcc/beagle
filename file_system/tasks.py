import logging
from celery import shared_task
from notifier.models import JobGroupNotifier

logger = logging.getLogger(__name__)


@shared_task
def populate_job_group_notifier_metadata(request_id, pi, investigator, assay):
    job_group_notifiers = JobGroupNotifier.objects.filter(
        request_id=request_id, PI__isnull=True, investigator__isnull=True, assay__isnull=True
    )
    for job_group_notifier in job_group_notifiers:
        logger.info(
            "Updating JobGroup {jg_id} with metadata requestId: {request_id} PI: {pi}, investigator: {investigator}, assay: {assay}".format(
                jg_id=str(job_group_notifier.id), request_id=request_id, pi=pi, investigator=investigator, assay=assay
            )
        )
        job_group_notifier.PI = pi
        job_group_notifier.investigator = investigator
        job_group_notifier.assay = assay
        job_group_notifier.save()
