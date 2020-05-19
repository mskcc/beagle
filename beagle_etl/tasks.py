import logging
import importlib
import datetime
import traceback
from celery import shared_task
from django.db import transaction
from beagle_etl.models import JobStatus, Job
from beagle_etl.jobs.lims_etl_jobs import TYPES
from file_system.repository import FileRepository
from notifier.tasks import send_notification
from notifier.helper import generate_sample_data_content
from notifier.events import ETLImportEvent, ETLJobsLinksEvent, ETLJobFailedEvent, SetCIReviewEvent, UploadAttachmentEvent


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
                    self.job.message = {"details": "Error: %s" % str(e)}
                    self._job_failed()
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
            if job.run == TYPES['SAMPLE']:
                if job.status == JobStatus.COMPLETED:
                    samples_completed.add(job.args['sample_id'])
                elif job.status == JobStatus.FAILED:
                    samples_failed.add(job.args['sample_id'])

            if job.run == TYPES['SAMPLE']:
                sample_jobs.append((str(job.id), JobStatus(job.status).name, self.get_key(job.run), job.message or "",
                                   job.args.get('sample_id', '')))
            elif job.run == TYPES['REQUEST']:
                request_jobs.append(
                    (str(job.id), '', self.get_key(job.run), job.message or "", ''))
            elif job.run == TYPES['POOLED_NORMAL']:
                pooled_normal_jobs.append(
                    (str(job.id), JobStatus(job.status).name, self.get_key(job.run), job.message or "",
                     job.args.get('sample_id', '')))

        all_jobs.extend(request_jobs)
        all_jobs.extend(sample_jobs)
        all_jobs.extend(pooled_normal_jobs)

        request_metadata = Job.objects.filter(args__request_id=self.job.args['request_id'], run=TYPES['SAMPLE']).first()

        number_of_tumors = FileRepository.filter(
            metadata={'requestId': self.job.args['request_id'], 'tumorOrNormal': 'Tumor'}, ret='sampleId').count()
        number_of_normals = FileRepository.filter(
            metadata={'requestId': self.job.args['request_id'], 'tumorOrNormal': 'Normal'}, ret='sampleId').count()

        data_analyst_email = ""
        data_analyst_name = ""
        investigator_email = ""
        investigator_name = ""
        lab_head_email = ""
        lab_head_name = ""
        pi_email = ""
        project_manager_name = ""
        recipe = ""

        if request_metadata:
            metadata = request_metadata.args.get('request_metadata', {})
            recipe = metadata['recipe']
            data_analyst_email = metadata['dataAnalystEmail']
            data_analyst_name = metadata['dataAnalystName']
            investigator_email = metadata['investigatorEmail']
            investigator_name = metadata['investigatorName']
            lab_head_email = metadata['labHeadEmail']
            lab_head_name = metadata['labHeadName']
            pi_email = metadata['piEmail']
            project_manager_name = metadata['projectManagerName']

        event = ETLImportEvent(str(self.job.job_group.id),
                               self.job.args['request_id'],
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
                               number_of_tumors,
                               number_of_normals,
                               len(pooled_normal_jobs)
                               )
        e = event.to_dict()
        send_notification.delay(e)

        etl_event = ETLJobsLinksEvent(str(self.job.job_group.id),
                                      self.job.args['request_id'],
                                      all_jobs)
        etl_e = etl_event.to_dict()
        send_notification.delay(etl_e)

    def _generate_sample_data_file(self):
        result = generate_sample_data_content(self.job.args['request_id'])
        e = UploadAttachmentEvent(str(self.job.job_group.id),
                                  '%s_sample_data_clinical.txt' % self.job.args['request_id'],
                                  result).to_dict()
        send_notification.delay(e)

    def _job_failed(self):
        if self.job.run == TYPES['REQUEST']:
            e = ETLJobFailedEvent(self.job.job_group.id,
                                  "[CIReviewEvent] ETL Job failed, likely child job import. Check pooled normal import, might already exist in database.").to_dict()
            send_notification.delay(e)
            ci_review = SetCIReviewEvent(str(self.job.job_group.id)).to_dict()
            send_notification.delay(ci_review)
            self._generate_ticket_decription()
            self._generate_sample_data_file()

    def _job_successful(self):
        if self.job.run == TYPES['REQUEST']:
            self._generate_ticket_decription()
            self._generate_sample_data_file()

    def _check_children(self):
        finished = True
        failed = []
        for child_id in self.job.children:
            try:
                child_job = Job.objects.get(id=child_id)
            except Job.DoesNotExist:
                failed.append(child_id)
                continue
            if child_job.status == JobStatus.FAILED:
                failed.append(child_id)
            if child_job.status in (JobStatus.IN_PROGRESS, JobStatus.CREATED, JobStatus.WAITING_FOR_CHILDREN):
                finished = False
                break
        if finished:
            if failed:
                self.job.status = JobStatus.FAILED
                self.job.message = {"details": "Child jobs %s failed" % ', '.join(failed)}
                self._job_failed()
            else:
                self.job.status = JobStatus.COMPLETED
                self._job_successful()
            if self.job.callback:
                job = Job(run=self.job.callback,
                          args=self.job.callback_args,
                          status=JobStatus.CREATED,
                          max_retry=1,
                          children=[],
                          job_group=self.job.job_group)
                job.save()
