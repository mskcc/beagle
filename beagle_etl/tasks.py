import pytz
import logging
import datetime
from celery import shared_task
from django.conf import settings
from beagle_etl.models import SMILEMessage, SmileMessageStatus, RequestCallbackJobStatus, RequestCallbackJob
from beagle_etl.jobs.metadb_jobs import (
    new_request,
    update_request_job,
    update_sample_job,
    request_callback,
)
from lib.memcache_lock import memcache_task_lock
from ddtrace import tracer
from django.db.models import Case, When, IntegerField


logger = logging.getLogger(__name__)


def get_pending_smile_messages():
    """
    Get pending SMILE messages ordered by topic priority and creation date.

    Returns messages in order: NEW_REQUEST, SAMPLE_UPDATE, REQUEST_UPDATE,
    with each group sorted by created_date.

    Returns:
        QuerySet of SMILEMessage objects
    """
    return (
        SMILEMessage.objects.filter(
            status=SmileMessageStatus.PENDING,
            topic__in=[
                settings.METADB_NATS_NEW_REQUEST,
                settings.METADB_NATS_SAMPLE_UPDATE,
                settings.METADB_NATS_REQUEST_UPDATE,
            ],
        )
        .annotate(
            topic_priority=Case(
                When(topic=settings.METADB_NATS_NEW_REQUEST, then=0),
                When(topic=settings.METADB_NATS_SAMPLE_UPDATE, then=1),
                When(topic=settings.METADB_NATS_REQUEST_UPDATE, then=2),
                default=3,
                output_field=IntegerField(),
            )
        )
        .order_by("topic_priority", "created_date")
    )


@shared_task
@tracer.wrap(service="beagle")
def process_smile_events():
    """Process pending SMILE messages in priority order."""
    messages = get_pending_smile_messages()

    for msg in messages:
        lock_id = f"lock_smile_{msg.request_id}"
        print(lock_id)
        with memcache_task_lock(lock_id, msg) as acquired:
            if acquired:
                msg.in_progress()
                current_span = tracer.current_span()
                current_span.set_tag("request.id", msg.request_id)
                logger.info(
                    f"Processing {str(msg.id)} with igoRequestId={msg.request_id} received on topic={msg.topic}"
                )
                if msg.topic == settings.METADB_NATS_NEW_REQUEST:
                    print("New Request")
                    new_request.delay(str(msg.id))
                elif msg.topic == settings.METADB_NATS_SAMPLE_UPDATE:
                    print("Update Sample")
                    update_sample_job(msg.id)
                elif msg.topic == settings.METADB_NATS_REQUEST_UPDATE:
                    print("Update Request")
                    update_request_job(msg.id)

    unknown_topics = SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING).exclude(
        topic__in=(
            settings.METADB_NATS_REQUEST_UPDATE,
            settings.METADB_NATS_SAMPLE_UPDATE,
            settings.METADB_NATS_NEW_REQUEST,
        )
    )

    for msg in unknown_topics:
        logger.error(f"Unknown subject: {msg.topic}")
        msg.add_log(f"Unknown subject: {msg.topic}")
        msg.not_supported()


@shared_task
def process_request_callback_jobs():
    requests = RequestCallbackJob.objects.filter(status=RequestCallbackJobStatus.PENDING)
    for request in requests:
        if datetime.datetime.now(tz=pytz.UTC) > request.created_date + datetime.timedelta(minutes=request.delay):
            logger.info(f"Submitting request callback {request.request_id}")
            request_callback.delay(
                request.request_id,
                request.recipe,
                request.fastq_metadata,
                request.samples,
                str(request.job_group.id),
                str(request.job_group_notifier.id),
            )
        request.status = RequestCallbackJobStatus.COMPLETED
        request.save()
