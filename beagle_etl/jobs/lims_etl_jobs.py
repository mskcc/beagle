import os
import copy
import logging
import requests
from django.conf import settings
from django.db.models import Prefetch
from runner.tasks import operator_job
from beagle_etl.models import JobStatus, Job, Operator
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.models import File, FileGroup, FileMetadata, FileType
from file_system.metadata.validator import MetadataValidator, METADATA_SCHEMA
from beagle_etl.exceptions import FailedToFetchFilesException, FailedToSubmitToOperatorException

logger = logging.getLogger(__name__)


TYPES = {
    "DELIVERY": "beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims",
    "REQUEST": "beagle_etl.jobs.lims_etl_jobs.fetch_samples",
    "SAMPLE": "beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata"
}


def fetch_new_requests_lims(timestamp):
    logger.info("Fetching requestIds")
    children = set()
    requestIds = requests.get('%s/LimsRest/api/getDeliveries' % settings.LIMS_URL,
                             params={"timestamp": timestamp},
                             auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if requestIds.status_code != 200:
        raise FailedToFetchFilesException("Failed to fetch new requests")
    if not requestIds.json():
        logger.info("There is no new RequestIDs")
        return []
    for request in requestIds.json():
        job = get_or_create_request_job(request['request'])
        if job.status == JobStatus.CREATED:
            children.add(str(job.id))
    return list(children)


def get_or_create_request_job(request_id):
    logger.info(
        "Searching for job: %s for request_id: %s" % ('beagle_etl.jobs.lims_etl_jobs.fetch_samples', request_id))
    job = Job.objects.filter(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args__request_id=request_id).first()
    if not job:
        op = Operator.objects.first()
        if op.active:
            job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args={'request_id': request_id},
                      status=JobStatus.CREATED, max_retry=1, children=[],
                      callback='beagle_etl.jobs.lims_etl_jobs.request_callback',
                      callback_args={'request_id': request_id})
            job.save()
        else:
            job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args={'request_id': request_id},
                      status=JobStatus.CREATED, max_retry=1, children=[])
            job.save()
    return job


def get_operator(recipe):
    if recipe in ("Agilent_51MB", "HumanWholeGenome", "ShallowWGS", "WholeExomeSequencing"):
        return 'tempo'
    elif recipe in ("IMPACT341", "IMPACT+ (341 genes plus custom content)", "IMPACT410", "IMPACT468"):
        return 'roslin'
    elif recipe in ("MSK-ACCESS_v1",):
        return "access"
    else:
        return None


def request_callback(request_id):
    # recipe = File.objects.filter(filemetadata__metadata__requestId=request_id).first().filemetadata_set.first().metadata.get('requestMetadata', {}).get('recipe', None)
    queryset = File.objects.prefetch_related(Prefetch('filemetadata_set',
                                                      queryset=FileMetadata.objects.select_related('file').order_by(
                                                          '-created_date'))).order_by('file_name').filter(
        filemetadata__metadata__requestId=request_id)
    ret_str = 'filemetadata__metadata__requestMetadata__recipe'
    recipes = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
    if not recipes:
        raise FailedToSubmitToOperatorException(
            "Not enough metadata to choose the operator for requestId:%s" % request_id)
    operator = get_operator(recipes[0])
    if not operator:
        logger.error("Submitting request_is: %s to  for requestId: %s to operator" % (request_id, operator))
        raise FailedToSubmitToOperatorException("Not operator defined for recipe: %s" % recipes[0])
    logger.info("Submitting request_id %s to %s operator" % (request_id, operator))
    operator_job.delay(request_id, operator)
    return []


def fetch_samples(request_id):
    logger.info("Fetching sampleIds for requestId:%s" % request_id)
    children = set()
    sampleIds = requests.get('%s/LimsRest/api/getRequestSamples' % settings.LIMS_URL,
                             params={"request": request_id},
                             auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleIds.status_code != 200:
        raise FailedToFetchFilesException("Failed to fetch sampleIds for request %s" % request_id)
    if sampleIds.json()['requestId'] != request_id:
        raise FailedToFetchFilesException("LIMS returned wrong response for request %s. Got %s instead" % (request_id, sampleIds.json()['requestId']))
    response_body = sampleIds.json()
    request_metadata = {
        "dataAnalystEmail": response_body['dataAnalystEmail'],
        "dataAnalystName": response_body['dataAnalystName'],
        "investigatorEmail": response_body['investigatorEmail'],
        "investigatorName": response_body['investigatorName'],
        "labHeadEmail": response_body['labHeadEmail'],
        "labHeadName": response_body['labHeadName'],
        "projectManagerName": response_body['projectManagerName'],
        "recipe": response_body['recipe'],
        "piEmail": response_body["piEmail"],
        "pooledNormals": response_body["pooledNormals"]
    }
    logger.info("Response: %s" % str(sampleIds.json()))
    for sample in response_body.get('samples', []):
        if not sample:
            raise FailedToFetchFilesException("Sample Id None")
        job = get_or_create_sample_job(sample['igoSampleId'], sample['igocomplete'], request_id, request_metadata)
        children.add(str(job.id))
    return list(children)


def get_or_create_sample_job(sample_id, igocomplete, request_id, request_metadata):
    logger.info(
        "Searching for job: %s for sample_id: %s" % ('beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', sample_id))
    job = Job.objects.filter(run='beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', args__sample_id=sample_id).first()
    if not job:
        job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata',
                  args={'sample_id': sample_id, 'igocomplete': igocomplete, 'request_id': request_id, 'request_metadata': request_metadata},
                  status=JobStatus.CREATED, max_retry=1, children=[])
        job.save()
    return job


def fetch_sample_metadata(sample_id, igocomplete, request_id, request_metadata):
    conflict = False
    missing_fastq = False
    conflict_files = []
    failed_runs = []
    logger.info("Fetch sample metadata for sampleId:%s" % sample_id)
    sampleMetadata = requests.get('%s/LimsRest/api/getSampleManifest' % settings.LIMS_URL,
                                  params={"igoSampleId": sample_id},
                                  auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleMetadata.status_code != 200:
        logger.error("Failed to fetch SampleManifest for sampleId:%s" % sample_id)
        raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s" % sample_id)
    try:
        data = sampleMetadata.json()[0]
    except Exception as e:
        raise FailedToFetchFilesException(
            "Failed to fetch SampleManifest for sampleId:%s. Invalid response" % sample_id)
    if data['igoId'] != sample_id:
        logger.info(data)
        logger.info("Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))
        raise FailedToFetchFilesException(
            "Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))
    libraries = data.pop('libraries')
    if not libraries:
        raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id)
    for library in libraries:
        logger.info("Processing library %s" % library)
        runs = library.pop('runs')
        if not runs:
            logger.error("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
            raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
        run_dict = convert_to_dict(runs)
        logger.info("Processing runs %s" % run_dict)
        for run in run_dict.values():
            logger.info("Processing run %s" % run)
            fastqs = run.pop('fastqs')
            if not fastqs:
                logger.error("Failed to fetch SampleManifest for sampleId:%s. Fastqs empty" % sample_id)
                missing_fastq = True
                failed_runs.append(run['runId'])
            else:
                file_search = File.objects.filter(path=fastqs[0]).first()
                if not file_search:
                    create_file(fastqs[0], request_id, settings.IMPORT_FILE_GROUP, 'fastq', igocomplete, data, library, run,
                                request_metadata, R1_or_R2(fastqs[0]))
                else:
                    logger.error("File %s already created with id:%s" % (file_search.path, str(file_search.id)))
                    conflict = True
                    conflict_files.append((file_search.path, str(file_search.id)))
                file_search = File.objects.filter(path=fastqs[1]).first()
                if not file_search:
                    create_file(fastqs[1], request_id, settings.IMPORT_FILE_GROUP, 'fastq', igocomplete, data, library, run,
                                request_metadata, R1_or_R2(fastqs[1]))
                else:
                    logger.error("File %s already created with id:%s" % (file_search.path, str(file_search.id)))
                    conflict = True
                    conflict_files.append((file_search.path, str(file_search.id)))
    if conflict:
        raise FailedToFetchFilesException(
            "Files %s already exists" % ' '.join(['%s with id: %s' % (cf[0], cf[1]) for cf in conflict_files]))
    if missing_fastq:
        raise FailedToFetchFilesException("Missing fastq files for %s : %s" % (sample_id, ' '.join(failed_runs)))


def R1_or_R2(filename):
    reversed_filename = ''.join(reversed(filename))
    R1_idx = reversed_filename.find('1R')
    R2_idx = reversed_filename.find('2R')
    if R1_idx == -1 and R2_idx == -1:
        return "ERROR"
    elif R1_idx > 0 and R2_idx == -1:
        return "R1"
    elif R2_idx > 0 and R1_idx == -1:
        return 'R2'
    elif R1_idx > 0 and R2_idx > 0:
        if R1_idx < R2_idx:
            return 'R1'
        else:
            return 'R2'
    return 'ERROR'


def convert_to_dict(runs):
    run_dict = dict()
    for run in runs:
        if not run_dict.get(run['runId']):
            run_dict[run['runId']] = run
        else:
            if run_dict[run['runId']].get('fastqs'):
                logger.error("Fastq empty")
                if run_dict[run['runId']]['fastqs'][0] != run['fastqs'][0]:
                    logger.error(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][0], run['fastqs'][0]))
                    raise FailedToFetchFilesException(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][0], run['fastqs'][0]))
                if run_dict[run['runId']]['fastqs'][1] != run['fastqs'][1]:
                    logger.error(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][1], run['fastqs'][1]))
                    raise FailedToFetchFilesException(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][1], run['fastqs'][1]))
    return run_dict


def create_file(path, request_id, file_group_id, file_type, igocomplete, data, library, run, request_metadata, r):
    logger.info("Creating file %s " % path)
    try:
        file_group_obj = FileGroup.objects.get(id=file_group_id)
        file_type_obj = FileType.objects.filter(ext=file_type).first()
        metadata = copy.deepcopy(data)
        metadata['requestId'] = request_id
        metadata['R'] = r
        metadata['igocomplete'] = igocomplete
        for k, v in library.items():
            metadata[k] = v
        for k, v in run.items():
            metadata[k] = v
        for k, v in request_metadata.items():
            metadata[k] = v
        # validator = MetadataValidator(METADATA_SCHEMA)
    except Exception as e:
        logger.error("Failed to parse metadata for file %s path" % path)
        raise FailedToFetchFilesException("Failed to create file %s. Error %s" % (path, str(e)))
    try:
        logger.info(metadata)
        # validator.validate(metadata)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchFilesException("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        try:
            f = File.objects.create(file_name=os.path.basename(path), path=path, file_group=file_group_obj,
                                    file_type=file_type_obj)
            f.save()
            fm = FileMetadata(file=f, metadata=metadata)
            fm.save()
        except Exception as e:
            logger.error("Failed to create file %s. Error %s" % (path, str(e)))
            raise FailedToFetchFilesException("Failed to create file %s. Error %s" % (path, str(e)))


def update_metadata(request_id):
    logger.info("Fetching sampleIds for requestId:%s" % request_id)
    children = set()
    sampleIds = requests.get('%s/LimsRest/api/getRequestSamples' % settings.LIMS_URL,
                             params={"request": request_id},
                             auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleIds.status_code != 200:
        raise FailedToFetchFilesException("Failed to fetch sampleIds for request %s" % request_id)
    if sampleIds.json()['requestId'] != request_id:
        raise FailedToFetchFilesException(
            "LIMS returned wrong response for request %s. Got %s instead" % (request_id, sampleIds.json()['requestId']))
    response_body = sampleIds.json()
    request_metadata = {
        "dataAnalystEmail": response_body['dataAnalystEmail'],
        "dataAnalystName": response_body['dataAnalystName'],
        "investigatorEmail": response_body['investigatorEmail'],
        "investigatorName": response_body['investigatorName'],
        "labHeadEmail": response_body['labHeadEmail'],
        "labHeadName": response_body['labHeadName'],
        "projectManagerName": response_body['projectManagerName'],
        "recipe": response_body['recipe'],
        "piEmail": response_body["piEmail"],
        "pooledNormals": response_body["pooledNormals"]
    }
    logger.info("Response: %s" % str(sampleIds.json()))
    for sample in response_body.get('samples', []):
        if not sample:
            raise FailedToFetchFilesException("Sample Id None")
        if sample['igocomplete']:
            job = update_sample_job(sample['igoSampleId'], request_id, request_metadata)
            children.add(str(job.id))
        else:
            logger.info("Sample %s not igoComplete" % str(sample['igoSampleId']))
    return list(children)


def update_sample_metadata(sample_id, request_id, request_metadata):
    missing = False
    missing_fastq = False
    failed_runs = []
    missing_files = []
    logger.info("Fetch sample metadata for sampleId:%s" % sample_id)
    sampleMetadata = requests.get('%s/LimsRest/api/getSampleManifest' % settings.LIMS_URL,
                                  params={"igoSampleId": sample_id},
                                  auth=(settings.LIMS_USERNAME, settings.LIMS_PASSWORD), verify=False)
    if sampleMetadata.status_code != 200:
        logger.error("Failed to fetch SampleManifest for sampleId:%s" % sample_id)
        raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s" % sample_id)
    try:
        data = sampleMetadata.json()[0]
    except Exception as e:
        raise FailedToFetchFilesException(
            "Failed to fetch SampleManifest for sampleId:%s. Invalid response" % sample_id)
    if data['igoId'] != sample_id:
        logger.info(data)
        logger.info("Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))
        raise FailedToFetchFilesException(
            "Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))
    libraries = data.pop('libraries')
    if not libraries:
        raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id)
    for library in libraries:
        logger.info("Processing library %s" % library)
        runs = library.pop('runs')
        if not runs:
            logger.error("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
            raise FailedToFetchFilesException("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
        run_dict = convert_to_dict(runs)
        logger.info("Processing runs %s" % run_dict)
        for run in run_dict.values():
            logger.info("Processing run %s" % run)
            fastqs = run.pop('fastqs')
            if not fastqs:
                logger.error("Failed to fetch SampleManifest for sampleId:%s. Fastqs empty" % sample_id)
                missing_fastq = True
                failed_runs.append(run['runId'])
            else:
                file_search = File.objects.filter(path=fastqs[0]).first()
                if file_search:
                    update_file_metadata(fastqs[0], request_id, data, library, run, request_metadata, 'R1')
                else:
                    logger.error("File %s missing" % file_search.path)
                    missing = True
                    missing_files.append((file_search.path, str(file_search.id)))
                file_search = File.objects.filter(path=fastqs[1]).first()
                if file_search:
                    update_file_metadata(fastqs[1], request_id, data, library, run, request_metadata, 'R2')
                else:
                    logger.error("File %s missing" % file_search.path)
                    missing = True
                    missing_files.append((file_search.path, str(file_search.id)))
    if missing:
        raise FailedToFetchFilesException(
            "Files %s missing" % ' '.join(['%s with id: %s' % (cf[0], cf[1]) for cf in missing_files]))
    if missing_fastq:
        raise FailedToFetchFilesException("Missing fastq files for %s : %s" % (sample_id, ' '.join(failed_runs)))


def update_file_metadata(path, request_id, data, library, run, request_metadata, r):
    metadata = copy.deepcopy(data)
    metadata['requestId'] = request_id
    metadata['R'] = r
    for k, v in library.items():
        metadata[k] = v
    for k, v in run.items():
        metadata[k] = v
    for k, v in request_metadata.items():
        metadata[k] = v
    file_search = File.objects.filter(path=path).first()
    if not file_search:
        raise FailedToFetchFilesException("Failed to find file %s." % (path))
    data = {
        "path": path,
        "metadata": metadata
    }
    logger.info(data)
    serializer = UpdateFileSerializer(file_search, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        logger.error("SERIALIZER NOT VALID %s" % serializer.errors)
        raise FailedToFetchFilesException("Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors))


def update_sample_job(sample_id, request_id, request_metadata):
    logger.info(
        "Searching for job: %s for sample_id: %s" % ('beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata', sample_id))
    job = Job(run='beagle_etl.jobs.lims_etl_jobs.update_sample_metadata',
                  args={'sample_id': sample_id, 'request_id': request_id, 'request_metadata': request_metadata},
                  status=JobStatus.CREATED, max_retry=1, children=[])
    job.save()
    return job
