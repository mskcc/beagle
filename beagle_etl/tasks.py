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


@shared_task
def process_job_with_lock(job_func_name, message_id):
    """
    Wrapper task that acquires a lock before executing the actual job.

    Args:
        job_func_name: Name of the job function to execute ('new_request', 'update_request_job', 'update_sample_job')
        message_id: The SMILEMessage ID to process
    """
    message = SMILEMessage.objects.get(id=message_id)
    lock_id = f"lock_smile_{message.request_id}"

    with memcache_task_lock(lock_id, message) as acquired:
        if not acquired:
            print(f"Could not acquire lock for request {message.request_id}, skipping job {job_func_name}")
            logger.info(f"Could not acquire lock for request {message.request_id}, skipping job {job_func_name}")
            return

        message.in_progress()
        if job_func_name == "new_request":
            new_request(message_id)
        elif job_func_name == "update_request_job":
            update_request_job(message_id)
        elif job_func_name == "update_sample_job":
            update_sample_job(message_id)
        else:
            logger.error(f"Unknown job function: {job_func_name}")
            raise ValueError(f"Unknown job function: {job_func_name}")


def get_pending_smile_messages():
    """
    Get the highest priority pending SMILE message for each request_id.

    For each request_id with pending messages, returns only the message with
    the highest priority (NEW_REQUEST > SAMPLE_UPDATE > REQUEST_UPDATE).

    This ensures that within a request_id, messages are processed sequentially
    in priority order, while different request_ids can process in parallel.

    Returns:
        QuerySet of SMILEMessage objects
    """
    from django.db.models import Min

    # Get all pending messages with priority
    pending_messages = SMILEMessage.objects.filter(
        status=SmileMessageStatus.PENDING,
        topic__in=[
            settings.METADB_NATS_NEW_REQUEST,
            settings.METADB_NATS_SAMPLE_UPDATE,
            settings.METADB_NATS_REQUEST_UPDATE,
        ],
    ).annotate(
        topic_priority=Case(
            When(topic=settings.METADB_NATS_NEW_REQUEST, then=0),
            When(topic=settings.METADB_NATS_SAMPLE_UPDATE, then=1),
            When(topic=settings.METADB_NATS_REQUEST_UPDATE, then=2),
            default=3,
            output_field=IntegerField(),
        )
    )

    # For each request_id, find the minimum priority (highest priority message)
    min_priorities = pending_messages.values("request_id").annotate(min_priority=Min("topic_priority"))

    # Build a dict of request_id -> min_priority
    min_priority_map = {item["request_id"]: item["min_priority"] for item in min_priorities}

    # Filter to only return the highest priority message per request_id
    result = []
    for request_id, min_priority in min_priority_map.items():
        highest_priority_msg = (
            pending_messages.filter(request_id=request_id, topic_priority=min_priority).order_by("created_date").first()
        )
        if highest_priority_msg:
            result.append(highest_priority_msg)

    return result


@shared_task
@tracer.wrap(service="beagle")
def process_smile_events():
    """Process pending SMILE messages in priority order."""
    messages = get_pending_smile_messages()
    logger.debug(f"Submitting {len(messages)} jobs")

    for msg in messages:
        current_span = tracer.current_span()
        current_span.set_tag("request.id", msg.request_id)
        logger.info(f"Processing {str(msg.id)} with igoRequestId={msg.request_id} received on topic={msg.topic}")
        if msg.topic == settings.METADB_NATS_NEW_REQUEST:
            logger.info(f"Submitting New Request {str(msg.id)}")
            process_job_with_lock.delay("new_request", str(msg.id))
        elif msg.topic == settings.METADB_NATS_SAMPLE_UPDATE:
            logger.info(f"Submitting Update Sample {str(msg.id)}")
            process_job_with_lock.delay("update_sample_job", str(msg.id))
        elif msg.topic == settings.METADB_NATS_REQUEST_UPDATE:
            logger.info(f"Submitting Update Request {str(msg.id)}")
            process_job_with_lock.delay("update_request_job", str(msg.id))

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
