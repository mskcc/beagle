import os
import copy
import logging
import requests
from django.conf import settings
from beagle_etl.models import JobStatus, Job
from file_system.exceptions import MetadataValidationException
from file_system.models import File, FileGroup, FileMetadata, FileType
from file_system.metadata.validator import MetadataValidator, METADATA_SCHEMA

logger = logging.getLogger(__name__)


def fetch_new_requests_lims():
    logger.info("Fetching requestIds")
    children = set()
    requestIds = requests.get('%s/LimsRest/getRecentDeliveries' % settings.LIMS_URL,
                              params={"time": 5, "units": "d"},
                              auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if requestIds.status_code != 200:
        raise Exception("Failed to fetch new requests")
    if not requestIds.json():
        logger.info("There is no new RequestIDs")
        return []
    for request in requestIds.json()[0].get('samples', []):
        job = get_or_create_request_job(request['project'])
        children.add(str(job.id))
    return list(children)


def get_or_create_request_job(request_id):
    logger.info(
        "Searching for job: %s for request_id: %s" % ('beagle_etl.jobs.lims_etl_jobs.fetch_samples', request_id))
    job = Job.objects.filter(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args__request_id=request_id).first()
    if not job or job.status == JobStatus.FAILED:
        job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args={'request_id': request_id},
                  status=JobStatus.CREATED, max_retry=3, children=[])
        job.save()
    return job


def fetch_samples(request_id):
    logger.info("Fetching sampleIds for requestId:%s" % request_id)
    children = set()
    sampleIds = requests.get('%s/LimsRest/api/getRequestSamples' % settings.LIMS_URL,
                             params={"request": request_id},
                             auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleIds.status_code != 200:
        raise Exception("Failed to fetch sampleIds for request %s" % request_id)
    for sample in sampleIds.json().get('samples', []):
        job = get_or_create_sample_job(sample['igoSampleId'])
        children.add(str(job.id))
    return list(children)


def get_or_create_sample_job(sample_id):
    logger.info(
        "Searching for job: %s for sample_id: %s" % ('beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', sample_id))
    job = Job.objects.filter(run='beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', args__sample_id=sample_id).first()
    if not job or job.status == JobStatus.FAILED:
        job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', args={'sample_id': sample_id},
                  status=JobStatus.CREATED, max_retry=3, children=[])
        job.save()
    return job


def fetch_sample_metadata(sample_id):
    sampleMetadata = requests.get('%s/LimsRest/api/getSampleManifest' % settings.LIMS_URL,
                                  params={"igoSampleId": sample_id},
                                  auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleMetadata.status_code != 200:
        raise Exception("Failed to Fetch SampleManifest for sampleId:%s" % sample_id)
    data = sampleMetadata.json()[0]
    libraries = data.pop('libraries')
    for library in libraries:
        runs = library.pop('runs')
        for run in runs:
            fastqs = run.pop('fastqs')
            if fastqs:
                file_search = File.objects.filter(path=fastqs[0]).first()
                if not file_search:
                    create_file(fastqs[0], sample_id, settings.IMPORT_FILE_GROUP, 'fastq', data,
                                library, run)
                else:
                    logger.info("File %s already created with id:%s" % (file_search.path, str(file_search.id)))
                file_search = File.objects.filter(path=fastqs[1]).first()
                if not file_search:
                    create_file(fastqs[1], sample_id, settings.IMPORT_FILE_GROUP, 'fastq', data,
                                library, run)
                else:
                    logger.info("File %s already created with id:%s" % (file_search.path, str(file_search.id)))


def create_file(path, sample_id, file_group_id, file_type, data, library, run):
    logger.info("Creating file %s " % path)
    file_group_obj = FileGroup.objects.get(id=file_group_id)
    file_type_obj = FileType.objects.filter(ext=file_type).first()
    metadata = copy.deepcopy(data)
    metadata['igoSampleId'] = sample_id
    metadata['libraries'] = [copy.deepcopy(library)]
    metadata['libraries'][0]['runs'] = [run]
    validator = MetadataValidator(METADATA_SCHEMA)
    try:
        logger.info(metadata)
        validator.validate(metadata)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        f = File.objects.create(file_name=os.path.basename(path), path=path, file_group=file_group_obj,
                                file_type=file_type_obj)
        f.save()
        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
        return True
    return False
