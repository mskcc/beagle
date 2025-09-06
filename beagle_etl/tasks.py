import pytz
import logging
import datetime
import asyncio
from celery import shared_task
from django.conf import settings
from beagle_etl.models import (
    SMILEMessage,
    SmileMessageStatus,
    RequestCallbackJobStatus,
    RequestCallbackJob,
    SkipProject,
)
from beagle_etl.nats_client.nats_client import run
from beagle_etl.jobs.metadb_jobs import (
    new_request,
    update_job,
    not_supported,
    request_callback,
)
from notifier.events import ETLImportEvent, ETLJobsLinksEvent, PermissionDeniedEvent, SendEmailEvent
from ddtrace import tracer

logger = logging.getLogger(__name__)


@shared_task
def fetch_request_nats():
    start_time = datetime.datetime.now(datetime.timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run(loop, settings.METADB_NATS_NEW_REQUEST, start_time))
    loop.run_forever()


@shared_task
@tracer.wrap(service="beagle")
def process_smile_events():
    update_requests = set()

    messages = list(
        SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING, topic=settings.METADB_NATS_REQUEST_UPDATE)
    )
    for msg in messages:
        update_requests.add(msg.request_id)
    messages = list(
        SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING, topic=settings.METADB_NATS_SAMPLE_UPDATE)
    )
    for msg in messages:
        update_requests.add("_".join(msg.request_id.split("_")[:-1]))

    messages = list(
        SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING, topic=settings.METADB_NATS_NEW_REQUEST)
    )
    for message in messages:
        if message.request_id in update_requests:
            update_requests.remove(message.request_id)
            current_span = tracer.current_span()
            request_id = message.request_id
            current_span.set_tag("request.id", request_id)
        logger.info(f"New request: {message.request_id}")
        message.in_progress()
        new_request.delay(str(message.id))

    for req in list(update_requests):
        logger.info(f"Update request/samples: {req}")
        req.in_progress()
        update_job.delay(req)

    unknown_topics = SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING).exclude(
        topic__in=(
            settings.METADB_NATS_REQUEST_UPDATE,
            settings.METADB_NATS_SAMPLE_UPDATE,
            settings.METADB_NATS_NEW_REQUEST,
        )
    )

    for msg in unknown_topics:
        msg.in_progress()
        not_supported.delay(str(msg.id))
        logger.error(f"Unknown subject: {msg.topic}")


@shared_task
def process_request_callback_jobs():
    requests = RequestCallbackJob.objects.filter(status=RequestCallbackJobStatus.PENDING)
    for request in requests:
        skip_projects_config = SkipProject.objects.first()
        if request.request_id in skip_projects_config.skip_projects:
            # TODO: Remove this when problem with redeliveries of old projects is gone
            pass
        elif datetime.datetime.now(tz=pytz.UTC) > request.created_date + datetime.timedelta(minutes=request.delay):
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
