import copy
import logging
import requests
from django.conf import settings
from celery import shared_task
from file_system.models import File, FileGroup, FileMetadata, FileType
from beagle_etl.models import RequestFetchJob, SamplesFetchJob, JobStatus, ETLError


logger = logging.getLogger(__name__)


@shared_task
def fetch_requests_lims():
    logger.info("Fetching requestIDs")
    requestIds = requests.get('https://igolims.mskcc.org:8443/LimsRest/getRecentDeliveries',
                              params={"time": 1, "units": "d"},
                              auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    for request in requestIds.json()[0].get('samples'):
        logger.info("Saving request %s" % request['project'])
        if RequestFetchJob.objects.filter(request_id=request['project']).first():
            logger.info("Request ID %s already processed" % request['project'])
            continue
        r = RequestFetchJob(request_id=request['project'], data=request, status=JobStatus.CREATED)
        r.save()
        fetch_samples_lims.delay(r.id)
    logger.info("Fetching requestIds job Completed")


@shared_task
def fetch_samples_lims(request_job_id):
    logger.info("Fetching sampleIds for requestId:%s" % request_job_id)
    try:
        request = RequestFetchJob.objects.get(pk=request_job_id)
    except RequestFetchJob.DoesNotExist:
        logger.info("Request ID %s already processed" % request_job_id)
        return
    sampleIds = requests.get('https://igolims.mskcc.org:8443/LimsRest/api/getRequestSamples',
                              params={"request": request.request_id},
                              auth=(settings.LIMS_USERNAME_NEW, settings.LIMS_PASSWORD_NEW), verify=False)
    if sampleIds.status_code != 200:
        ETLError(job_id=request_job_id, error={"details": "Failed to fetch samples for requestId:%s" % request.request_id})
        request.status = JobStatus.FAILED
    else:
        for sample in sampleIds.json().get('samples', []):
            logger.info("Saving sample %s" % sample['igoSampleId'])
            if SamplesFetchJob.objects.filter(sample_id=sample['igoSampleId']).first():
                logger.info("Sample ID %s already processed" % sample['igoSampleId'])
            s = SamplesFetchJob(sample_id=sample['igoSampleId'], data=sample, status=JobStatus.CREATED)
            s.save()
            fetch_sample_metadata.delay(s.id)
        request.status = JobStatus.PROCESSED
    request.save()
    logger.info("Fetching sampleIds job Completed")


@shared_task
def fetch_sample_metadata(sample_job_id):
    logger.info("Fetching sampleMetadata for SampleId:%s" % sample_job_id)
    file_group = FileGroup.objects.first()
    try:
        sample = SamplesFetchJob.objects.get(pk=sample_job_id)
    except SamplesFetchJob.DoesNotExist:
        logger.info("Request ID %s already processed" % sample_job_id)
        return
    sampleMetadata = requests.get('https://igolims.mskcc.org:8443/LimsRest/api/getSampleManifest',
                                  params={"igoSampleId": sample.sample_id},
                                  auth=(settings.LIMS_USERNAME_NEW, settings.LIMS_PASSWORD_NEW), verify=False)
    if sampleMetadata.status_code != 200:
        ETLError(job_id=sample_job_id,
                 error={"details": "Failed to fetch sample metadata for requestId:%s" % sample.sample_id})
        sample.status = JobStatus.FAILED
    else:
        data = sampleMetadata.json()[0]
        libraries = data.pop('libraries')
        runs = libraries[0].pop('runs')
        for run in runs:
            fastqs = run.pop('fastqs')
            if fastqs:
                file_search = File.objects.filter(path=fastqs[0]).first()
                if not file_search:
                    f = File.objects.create(path=fastqs[0], file_group=file_group,
                                        file_type=FileType.objects.filter(ext='fastq').first())
                    metadata = copy.deepcopy(data)
                    metadata['cmoSampleId'] = sample.sample_id
                    metadata['libraries'] = copy.deepcopy(libraries)
                    metadata['libraries'][0]['runs'] = [run]
                    logger.info(metadata)
                    fm = FileMetadata(file=f, metadata=metadata)
                    fm.save()
                else:
                    logger.info("File %s already created with id:%s" % (file_search.path, str(file_search.id)))
                file_search = File.objects.filter(path=fastqs[1]).first()
                if not file_search:
                    f = File.objects.create(path=fastqs[1], file_group=file_group,
                                            file_type=FileType.objects.filter(ext='fastq').first())
                    metadata = copy.deepcopy(data)
                    metadata['cmoSampleId'] = sample.sample_id
                    metadata['libraries'] = copy.deepcopy(libraries)
                    metadata['libraries'][0]['runs'] = [run]
                    logger.info(metadata)
                    fm = FileMetadata(file=f, metadata=metadata)
                    fm.save()
                else:
                    logger.info("File %s already created with id:%s" % (file_search.path, str(file_search.id)))
            else:
                error = ETLError(job_id=sample_job_id, type="MISSING_FASTQ", error={"details": "Fastq files not set %s" % run['runId']})
                sample.status = JobStatus.FAILED
                error.save()
        if sample.status != JobStatus.FAILED:
            sample.status = JobStatus.PROCESSED
        sample.save()


