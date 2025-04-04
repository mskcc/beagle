import pytz
import logging
import importlib
import datetime
import asyncio
from celery import shared_task
from lib.logger import format_log
from django.conf import settings
from beagle_etl.models import (
    JobStatus,
    Job,
    SMILEMessage,
    SmileMessageStatus,
    RequestCallbackJobStatus,
    RequestCallbackJob,
    SkipProject,
)
from beagle_etl.jobs.metadb_jobs import TYPES
from beagle_etl.exceptions import ETLExceptions
from beagle_etl.nats_client.nats_client import run
from beagle_etl.jobs.metadb_jobs import (
    new_request,
    update_job,
    not_supported,
    request_callback,
)
from file_system.repository import FileRepository
from notifier.tasks import send_notification
from notifier.events import ETLImportEvent, ETLJobsLinksEvent, PermissionDeniedEvent, SendEmailEvent
from ddtrace import tracer

logger = logging.getLogger(__name__)


@shared_task
def fetch_request_nats():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run(loop, settings.METADB_NATS_NEW_REQUEST))
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
        new_request.delay(str(message.id))

    for req in list(update_requests):
        logger.info(f"Update request/samples: {req}")
        update_job.delay(req)

    unknown_topics = SMILEMessage.objects.filter(status=SmileMessageStatus.PENDING).exclude(
        topic__in=(
            settings.METADB_NATS_REQUEST_UPDATE,
            settings.METADB_NATS_SAMPLE_UPDATE,
            settings.METADB_NATS_NEW_REQUEST,
        )
    )

    for msg in unknown_topics:
        not_supported.delay(str(msg.id))
        logger.error("Unknown subject: %s" % msg.topic)


@shared_task
def process_request_callback_jobs():
    requests = RequestCallbackJob.objects.filter(status=RequestCallbackJobStatus.PENDING)
    for request in requests:
        skip_projects_config = SkipProject.objects.first()
        if request.request_id in skip_projects_config.skip_projects:
            # TODO: Remove this when problem with redeliveries of old projects is gone
            pass
        elif datetime.datetime.now(tz=pytz.UTC) > request.created_date + datetime.timedelta(minutes=request.delay):
            logger.info("Submitting request callback %s" % request.request_id)
            request_callback.delay(
                request.request_id,
                request.recipe,
                request.samples,
                str(request.job_group.id),
                str(request.job_group_notifier.id),
            )
        request.status = RequestCallbackJobStatus.COMPLETED
        request.save()


@shared_task
def check_missing_requests():
    # TODO: Deprecated remove this
    """
    Method implemented because some requests on LIMS can show up with the date from the past
    """
    logger.info("ETL Check for missing requests")
    timestamp = int((datetime.datetime.now() - datetime.timedelta(hours=12)).timestamp()) * 1000

    job = Job(
        run="beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims",
        args={"timestamp": timestamp, "redelivery": False},
        status=JobStatus.CREATED,
        max_retry=3,
        children=[],
    )
    job.save()
    logger.info(format_log("ETL fetch_new_requests_lims job created", obj=job))


@shared_task
def job_processor(job_id):
    # TODO: Deprecated remove this
    logger.info(format_log("ETL Creating job", obj_id=job_id))
    job = JobObject(job_id)
    logger.info(format_log("ETL Processing job with args %s" % str(job.job.args), obj=job.job))
    job.process()


@shared_task
def scheduler():
    # TODO: Deprecated remove this
    jobs = get_pending_jobs()
    logger.info("Pending jobs: %s" % jobs)
    for job in jobs:
        j = Job.objects.get(id=job.id)
        if not j.is_locked:
            j.lock_job()
            logger.info(format_log("ETL submitting job", obj=job))
            job_processor.delay(j.id)
        else:
            logger.info(format_log("ETL job already locked", obj=job))


def get_pending_jobs():
    # TODO: Deprecated remove this
    jobs = Job.objects.filter(
        status__in=(JobStatus.CREATED, JobStatus.IN_PROGRESS, JobStatus.WAITING_FOR_CHILDREN), lock=False
    ).iterator()
    return jobs


class JobObject(object):
    # TODO: Deprecated remove this
    logger = logging.getLogger(__name__)

    def __init__(self, job_id):
        self.job = Job.objects.get(id=job_id)

    def process(self):
        if self.job.status == JobStatus.CREATED:
            self.job.status = JobStatus.IN_PROGRESS

        elif self.job.status == JobStatus.IN_PROGRESS:
            self.job.retry_count = self.job.retry_count + 1
            try:
                self._process()
                self.job.status = JobStatus.WAITING_FOR_CHILDREN
            except Exception as e:
                if isinstance(e, ETLExceptions):
                    message = {"message": str(e), "code": e.code}
                else:
                    message = {"message": str(e)}
                if self.job.retry_count == self.job.max_retry:
                    self.job.status = JobStatus.FAILED
                    self.job.message = message
                    self._job_failed()

        elif self.job.status == JobStatus.WAITING_FOR_CHILDREN:
            self._check_children()

        logger.info(format_log("ETL job in status: %s" % JobStatus(self.job.status).name, obj=self.job))
        self._unlock()
        self._save()

    def _unlock(self):
        self.job.unlock_job()

    def _save(self):
        self.job.save()

    def _process(self):
        mod_name, func_name = self.job.run.rsplit(".", 1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        children = func(**self.job.args)
        self.job.children = children or []

    def get_key(self, val):
        for key, value in TYPES.items():
            if val == value:
                return key
        return None

    def _generate_ticket_decription(self):
        samples_completed = set()
        samples_failed = set()
        all_jobs = []
        request_jobs = []
        sample_jobs = []
        pooled_normal_jobs = []

        jobs = Job.objects.filter(job_group=self.job.job_group.id).all()

        for job in jobs:
            if job.run == TYPES["SAMPLE"]:
                if job.status == JobStatus.COMPLETED:
                    samples_completed.add(job.args["sample_id"])
                elif job.status == JobStatus.FAILED:
                    samples_failed.add(job.args["sample_id"])

            if job.run == TYPES["SAMPLE"]:
                sample_jobs.append(
                    (
                        str(job.id),
                        JobStatus(job.status).name,
                        self.get_key(job.run),
                        job.message or "",
                        job.args.get("sample_id", ""),
                    )
                )
            elif job.run == TYPES["REQUEST"]:
                request_jobs.append((str(job.id), "", self.get_key(job.run), job.message or "", ""))
            elif job.run == TYPES["POOLED_NORMAL"]:
                pooled_normal_jobs.append(
                    (
                        str(job.id),
                        JobStatus(job.status).name,
                        self.get_key(job.run),
                        job.message or "",
                        job.args.get("sample_id", ""),
                    )
                )

        all_jobs.extend(request_jobs)
        all_jobs.extend(sample_jobs)
        all_jobs.extend(pooled_normal_jobs)

        request_metadata = (
            Job.objects.filter(args__request_id=self.job.args["request_id"], run=TYPES["SAMPLE"])
            .order_by("-created_date")
            .first()
        )

        number_of_tumors = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: self.job.args["request_id"], "tumorOrNormal": "Tumor"},
            values_metadata=settings.SAMPLE_ID_METADATA_KEY,
        ).count()
        number_of_normals = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: self.job.args["request_id"], "tumorOrNormal": "Normal"},
            values_metadata=settings.SAMPLE_ID_METADATA_KEY,
        ).count()

        data_analyst_email = ""
        data_analyst_name = ""
        investigator_email = ""
        investigator_name = ""
        lab_head_email = ""
        lab_head_name = ""
        pi_email = ""
        project_manager_name = ""
        recipe = ""
        qc_access_emails = ""
        data_access_emails = ""
        other_contact_emails = ""

        if request_metadata:
            metadata = request_metadata.args.get("request_metadata", {})
            recipe = metadata[settings.RECIPE_METADATA_KEY]
            data_analyst_email = metadata["dataAnalystEmail"]
            data_analyst_name = metadata["dataAnalystName"]
            investigator_email = metadata["investigatorEmail"]
            investigator_name = metadata["investigatorName"]
            lab_head_email = metadata["labHeadEmail"]
            lab_head_name = metadata["labHeadName"]
            pi_email = metadata["piEmail"]
            project_manager_name = metadata["projectManagerName"]
            qc_access_emails = metadata["qcAccessEmails"]
            data_access_emails = metadata["dataAccessEmails"]
            other_contact_emails = metadata["otherContactEmails"]

        event = ETLImportEvent(
            str(self.job.job_group_notifier.id),
            str(self.job.job_group.id),
            self.job.args["request_id"],
            list(samples_completed),
            list(samples_failed),
            recipe,
            data_analyst_email,
            data_analyst_name,
            investigator_email,
            investigator_name,
            lab_head_email,
            lab_head_name,
            pi_email,
            project_manager_name,
            qc_access_emails,
            number_of_tumors,
            number_of_normals,
            len(pooled_normal_jobs),
            data_access_emails,
            other_contact_emails,
        )
        e = event.to_dict()
        send_notification.delay(e)

        etl_event = ETLJobsLinksEvent(str(self.job.job_group_notifier.id), self.job.args["request_id"], all_jobs)
        etl_e = etl_event.to_dict()
        send_notification.delay(etl_e)

    def _job_failed(self, permission_denied=False, recipe=None):
        if self.job.run == TYPES["REQUEST"]:
            if permission_denied:
                cc = settings.PERMISSION_DENIED_CC.get(recipe, "")
                permission_denied_event = PermissionDeniedEvent(
                    self.job.job_group_notifier.id, "Failed to copy files because of the Permission denied issue", cc
                ).to_dict()
                send_notification.delay(permission_denied_event)
                emails = settings.PERMISSION_DENIED_EMAILS.get(recipe, "").split(",")
                for email in emails:
                    content = (
                        "Request failed to be imported because some files don't have proper permissions. "
                        "Check more details on %s/v0/etl/jobs/%s/" % (settings.BEAGLE_URL, str(self.job.id))
                    )
                    email = SendEmailEvent(
                        job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP,
                        email_to=email,
                        email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                        subject="Permission Denied for request_id: %s" % self.job.args.get("request_id"),
                        content=content,
                    )
                    send_notification.delay(email.to_dict())
            self._generate_ticket_decription()

    def _job_successful(self):
        if self.job.run == TYPES["REQUEST"]:
            self._generate_ticket_decription()

    def _check_children(self):
        finished = True
        failed = []
        permission_denied = False
        recipe = None
        for child_id in self.job.children:
            try:
                child_job = Job.objects.get(id=child_id)
            except Job.DoesNotExist:
                failed.append(child_id)
                continue
            if child_job.status == JobStatus.FAILED:
                failed.append(child_id)
                if isinstance(child_job.message, dict) and child_job.message.get("code", 0) == 108:
                    logger.error(format_log("ETL job failed because of permission denied error", obj=self.job))
                    recipe = child_job.args.get("request_metadata", {}).get(settings.RECIPE_METADATA_KEY)
                    permission_denied = True
            if child_job.status in (JobStatus.IN_PROGRESS, JobStatus.CREATED, JobStatus.WAITING_FOR_CHILDREN):
                finished = False
                break
        if finished:
            if failed:
                self.job.status = JobStatus.FAILED
                self.job.message = {"details": "Child jobs %s failed" % ", ".join(failed)}
                self._job_failed(permission_denied, recipe)
            else:
                self.job.status = JobStatus.COMPLETED
                self._job_successful()
            if self.job.callback:
                job = Job(
                    run=self.job.callback,
                    args=self.job.callback_args,
                    status=JobStatus.CREATED,
                    max_retry=1,
                    children=[],
                    job_group=self.job.job_group,
                )
                job.save()
