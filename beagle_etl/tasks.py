import logging
import importlib
import datetime
from celery import shared_task
from django.db import transaction
from django.db.models import Prefetch
from beagle_etl.models import JobStatus, Job
from file_system.models import File, FileMetadata
from beagle_etl.jobs.lims_etl_jobs import TYPES
from notifier.tasks import send_notification
from notifier.events import ETLImportEvent
from django.core.serializers import serialize, deserialize
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
import traceback


logger = logging.getLogger(__name__)


@shared_task
def fetch_requests_lims():
    logger.info("Fetching requestIDs")
    latest = Job.objects.filter(run=TYPES['DELIVERY']).order_by('-created_date').first()
    timestamp = None
    if latest:
        timestamp = int(latest.created_date.timestamp()) * 1000
    else:
        timestamp = int((datetime.datetime.now() - datetime.timedelta(hours=120)).timestamp()) * 1000
    job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims', args={'timestamp': timestamp},
              status=JobStatus.CREATED,
              max_retry=3, children=[])
    job.save()
    logger.info("Fetching fetch_new_requests_lims job created")


@shared_task
def job_processor(job_id):
    logger.info("Creating job: %s" % str(job_id))
    job = JobObject(job_id)
    logger.info("Processing job: %s with args: %s" % (str(job.job.id), str(job.job.args)))
    job.process()


@shared_task
def scheduler():
    jobs = get_pending_jobs()
    logger.info("Pending jobs: %s" % jobs)
    for job in jobs:
        with transaction.atomic():
            j = Job.objects.get(id=job.id)
            if not j.lock:
                logger.info("Submitting job: %s" % str(job.id))
                j.lock = True
                j.save()
                job_processor.delay(j.id)
            else:
                logger.info("Job already locked: %s" % str(job.id))


def get_pending_jobs():
    jobs = Job.objects.filter(status__in=(JobStatus.CREATED, JobStatus.IN_PROGRESS, JobStatus.WAITING_FOR_CHILDREN))
    return jobs


class JobObject(object):
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
                if self.job.retry_count == self.job.max_retry:
                    self.job.status = JobStatus.FAILED
                    self.job.message = {"details": "Error: %s" % traceback.format_tb(e.__traceback__)}
                    traceback.print_tb(e.__traceback__)

        elif self.job.status == JobStatus.WAITING_FOR_CHILDREN:
            self._check_children()

        with transaction.atomic():
            self.job.lock = False
            self.job.save()

        logger.info("Job %s in status: %s" % (str(self.job.id), JobStatus(self.job.status).name))
        self._save()

    def _save(self):
        self.job.save()

    def _process(self):
        mod_name, func_name = self.job.run.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        func = getattr(mod, func_name)
        children = func(**self.job.args)
        self.job.children = children or []

    def _job_successful(self):
        if self.job.run == TYPES['REQUEST']:
            successful_files = []
            successful = Job.objects.filter(args__request_id=self.job.args['request_id'], run=TYPES['SAMPLE'],
                                            status=JobStatus.COMPLETED)
            for job in successful:
                queryset = File.objects.prefetch_related(
                    Prefetch('filemetadata_set', queryset=
                    FileMetadata.objects.select_related('file').order_by('-created_date'))). \
                    order_by('file_name').filter(filemetadata__metadata__requestId=self.job.args['request_id'],
                                                 filemetadata__metadata__sampleId=job.args['sample_id']).all()
                for file in queryset:
                    successful_files.append((job.args['sample_id'], file.path))
            pooled_normals_files = []
            pooled_normals = Job.objects.filter(args__requestId=self.job.args['request_id'], run=TYPES['POOLED_NORMAL'],
                                                status=JobStatus.COMPLETED)
            for job in pooled_normals:
                pooled_normals_files.append(job.args['filepath'])

            event = ETLImportEvent(self.job.args['request_id'], successful_files, pooled_normals_files)
            e = event.to_dict()
            send_notification.delay(e)

            if Job.objects.filter(args__requestId=self.job.args['request_id'], status=JobStatus.FAILED):
                # self.notifier.request_finished(self.job.args['request_id'], "Hold")
                pass

    def _check_children(self):
        status = JobStatus.COMPLETED
        message = []
        for child_id in self.job.children:
            try:
                child_job = Job.objects.get(id=child_id)
            except Job.DoesNotExist:
                status = JobStatus.FAILED
                self.job.message = {"details": "Child job %s does't exist!" % child_id}
                break
            if child_job.status == JobStatus.FAILED:
                status = JobStatus.FAILED
                message.append(child_id)
                break
            if child_job.status in (JobStatus.IN_PROGRESS, JobStatus.CREATED):
                status = JobStatus.WAITING_FOR_CHILDREN
                break
        self.job.status = status
        if message:
            self.job.message = {"details": "Child jobs %s failed" % ', '.join(message)}
        if self.job.status == JobStatus.COMPLETED:
            self._job_successful()
            if self.job.callback:
                job = Job(run=self.job.callback,
                          args=self.job.callback_args,
                          status=JobStatus.CREATED,
                          max_retry=1,
                          children=[],
                          job_group=self.job.job_group)
                job.save()
