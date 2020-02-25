import os
import copy
import logging
import requests
from django.conf import settings
from django.db.models import Prefetch
from beagle_etl.models import JobStatus, Job, Operator
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.models import File, FileGroup, FileMetadata, FileType
from file_system.metadata.validator import MetadataValidator, METADATA_SCHEMA
from beagle_etl.exceptions import FailedToFetchFilesException, FailedToSubmitToOperatorException
from runner.tasks import create_jobs_from_request

logger = logging.getLogger(__name__)


TYPES = {
    "DELIVERY": "beagle_etl.jobs.lims_etl_jobs.fetch_new_requests_lims",
    "REQUEST": "beagle_etl.jobs.lims_etl_jobs.fetch_samples",
    "SAMPLE": "beagle_etl.jobs.lims_etl_jobs.fetch_sample_metadata",
    "POOLED_NORMAL": "beagle_etl.jobs.lims_etl_jobs.create_pooled_normal",
    "REQUEST_CALLBACK": "beagle_etl.jobs.lims_etl_jobs.request_callback",
    "UPDATE_SAMPLE_METADATA": "beagle_etl.jobs.lims_etl_jobs.update_sample_metadata"
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
        "Searching for job: %s for request_id: %s" % (TYPES['REQUEST'], request_id))
    job = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id).first()

    if not job:
        job = Job(run=TYPES['REQUEST'], args={'request_id': request_id},
                  status=JobStatus.CREATED, max_retry=1, children=[],
                  callback=TYPES['REQUEST_CALLBACK'],
                  callback_args={'request_id': request_id})
        job.save()
    return job


def request_callback(request_id):
    queryset = File.objects.prefetch_related(Prefetch('filemetadata_set',
                                                      queryset=FileMetadata.objects.select_related('file').order_by(
                                                          '-created_date'))).order_by('file_name').filter(
        filemetadata__metadata__requestId=request_id)
    ret_str = 'filemetadata__metadata__recipe'
    recipes = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
    if not recipes:
        raise FailedToSubmitToOperatorException(
           "Not enough metadata to choose the operator for requestId:%s" % request_id)

    operator = Operator.objects.get(
        active=True,
        recipes__contains=[recipes[0]]
    )
    if not operator:
        logger.error("Submitting request_is: %s to  for requestId: %s to operator" % (request_id, operator))
        raise FailedToSubmitToOperatorException("Not operator defined for recipe: %s" % recipes[0])
    logger.info("Submitting request_id %s to %s operator" % (request_id, operator.class_name))
    create_jobs_from_request.delay(request_id, operator.id)
    return []


def fetch_samples(request_id, import_pooled_normals=True, import_samples=True):
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
    }
    pooled_normals = response_body.get("pooledNormals", [])
    if import_pooled_normals:
        for f in pooled_normals:
            job = get_or_create_pooled_normal_job(f)
            children.add(str(job.id))
    logger.info("Response: %s" % str(sampleIds.json()))
    if import_samples:
        for sample in response_body.get('samples', []):
            if not sample:
                raise FailedToFetchFilesException("Sample Id None")
            job = get_or_create_sample_job(sample['igoSampleId'], sample['igocomplete'], request_id, request_metadata)
            children.add(str(job.id))
    return list(children)


def get_or_create_pooled_normal_job(filepath):
    logger.info(
        "Searching for job: %s for filepath: %s" % (TYPES['POOLED_NORMAL'], filepath))
    job = Job.objects.filter(run=TYPES['POOLED_NORMAL'], args__filepath=filepath).first()
    if not job:
        job = Job(run=TYPES['POOLED_NORMAL'],
                  args={'filepath': filepath, 'file_group_id': str(settings.POOLED_NORMAL_FILE_GROUP)},
                  status=JobStatus.CREATED, max_retry=1, children=[])
        job.save()
    return job


def get_or_create_sample_job(sample_id, igocomplete, request_id, request_metadata):
    logger.info(
        "Searching for job: %s for sample_id: %s" % (TYPES['SAMPLE'], sample_id))
    job = Job.objects.filter(run=TYPES['SAMPLE'], args__sample_id=sample_id).first()
    if not job:
        job = Job(run=TYPES['SAMPLE'],
                  args={'sample_id': sample_id, 'igocomplete': igocomplete, 'request_id': request_id,
                        'request_metadata': request_metadata},
                  status=JobStatus.CREATED, max_retry=1, children=[])
        job.save()
    return job


def get_run_id_from_string(string):
    """
    Parse the runID from a character string
    Split on the final '_' in the string

    Examples
    --------
        get_run_id_from_string("JAX_0397_BHCYYWBBXY")
        >>> JAX_0397
    """
    parts = string.split('_')
    if len(parts) > 1:
        parts.pop(-1)
        output = '_'.join(parts)
        return(output)
    else:
        return(string)


def create_pooled_normal(filepath, file_group_id):
    """
    Parse the file path provided for a Pooled Normal sample into the metadata fields needed to
    create the File and FileMetadata entries in the database

    Parameters:
    -----------
    filepath: str
        path to file for the sample
    file_group_id: UUID
        primary key for FileGroup to use for imported File entry

    Examples
    --------
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_POOLEDNORMALS/Sample_FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG/FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG_S5_R1_001.fastq.gz"
        file_group_id = settings.IMPORT_FILE_GROUP
        create_pooled_normal(filepath, file_group_id)

    Notes
    -----
    For filepath string such as "JAX_0397_BHCYYWBBXY";
    - runId = JAX_0397
    - flowCellId = HCYYWBBXY
    - [A|B] might be the flowcell bay the flowcell is placed into
    """
    if File.objects.filter(path=filepath):
        logger.info("Pooled normal already created filepath")
    file_group_obj = FileGroup.objects.get(id=file_group_id)
    file_type_obj = FileType.objects.filter(name='fastq').first()
    run_id = None
    preservation_type = None
    recipe = None
    try:
        parts = filepath.split('/')
        run_id = get_run_id_from_string(parts[6])
        preservation_type = parts[8]
        preservation_type = preservation_type.split('Sample_')[1]
        preservation_type = preservation_type.split('POOLEDNORMAL')[0]
        recipe = parts[8]
        recipe = recipe.split('IGO_')[1]
        recipe = recipe.split('_')[0]
    except Exception as e:
        raise FailedToFetchFilesException("Failed to parse metadata for pooled normal file %s" % filepath)
    if preservation_type not in ('FFPE', 'FROZEN', 'MOUSE'):
        raise FailedToFetchFilesException("Invalid preservation type %s" % preservation_type)
    if None in [run_id, preservation_type, recipe]:
        raise FailedToFetchFilesException(
            "Invalid metadata runId:%s preservation:%s recipe:%s" % (run_id, preservation_type, recipe))
    metadata = {
        "runId": run_id,
        "preservation": preservation_type,
        "recipe": recipe
    }
    try:
        f = File.objects.create(file_name=os.path.basename(filepath), path=filepath, file_group=file_group_obj,
                                file_type=file_type_obj)
        f.save()
        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
    except Exception as e:
        logger.error("Failed to create file %s. Error %s" % (filepath, str(e)))
        raise FailedToFetchFilesException("Failed to create file %s. Error %s" % (filepath, str(e)))


def fetch_sample_metadata(sample_id, igocomplete, request_id, request_metadata):
    conflict = False
    missing_fastq = False
    invalid_number_of_fastq = False
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
        # logger.info(data)
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
            elif len(fastqs) != 2:
                logger.error(
                    "Failed to fetch SampleManifest for sampleId:%s. %s fastq file(s) provided" % (
                    sample_id, str(len(fastqs))))
                invalid_number_of_fastq = True
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
    if invalid_number_of_fastq:
        raise FailedToFetchFilesException(
            "%s fastq file(s) provided: %s" % (str(len(failed_runs)), ' '.join(failed_runs)))


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
        file_type_obj = FileType.objects.filter(name=file_type).first()
        metadata = copy.deepcopy(data)
        sample_name = metadata.pop('cmoSampleName', None)
        external_sample_name = metadata.pop('sampleName', None)
        sample_id = metadata.pop('igoId', None)
        patient_id = metadata.pop('cmoPatientId', None)
        sample_class = metadata.pop('cmoSampleClass', None)
        metadata['requestId'] = request_id
        metadata['sampleName'] = sample_name
        metadata['externalSampleId'] = external_sample_name
        metadata['sampleId'] = sample_id
        metadata['patientId'] = patient_id
        metadata['sampleClass'] = sample_class
        metadata['R'] = r
        metadata['igocomplete'] = igocomplete
        metadata['libraryId'] = library.pop('libraryIgoId', None)
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
        job = update_sample_job(sample['igoSampleId'], sample['igocomplete'], request_id, request_metadata)
        children.add(str(job.id))
    return list(children)


def update_sample_metadata(sample_id, igocomplete, request_id, request_metadata):
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
                    update_file_metadata(fastqs[0], request_id, igocomplete, data, library, run, request_metadata,
                                         R1_or_R2(fastqs[0]))
                else:
                    logger.error("File %s missing" % file_search.path)
                    missing = True
                    missing_files.append((file_search.path, str(file_search.id)))
                file_search = File.objects.filter(path=fastqs[1]).first()
                if file_search:
                    update_file_metadata(fastqs[1], request_id, igocomplete, data, library, run, request_metadata,
                                         R1_or_R2(fastqs[1]))
                else:
                    logger.error("File %s missing" % file_search.path)
                    missing = True
                    missing_files.append((file_search.path, str(file_search.id)))
    if missing:
        raise FailedToFetchFilesException(
            "Files %s missing" % ' '.join(['%s with id: %s' % (cf[0], cf[1]) for cf in missing_files]))
    if missing_fastq:
        raise FailedToFetchFilesException("Missing fastq files for %s : %s" % (sample_id, ' '.join(failed_runs)))


def update_file_metadata(path, request_id, igocomplete, data, library, run, request_metadata, r):
    metadata = copy.deepcopy(data)
    sample_name = metadata.pop('cmoSampleName', None)
    external_sample_name = metadata.pop('sampleName', None)
    sample_id = metadata.pop('igoId', None)
    patient_id = metadata.pop('cmoPatientId', None)
    sample_class = metadata.pop('cmoSampleClass', None)
    metadata['requestId'] = request_id
    metadata['sampleName'] = sample_name
    metadata['externalSampleId'] = external_sample_name
    metadata['sampleId'] = sample_id
    metadata['patientId'] = patient_id
    metadata['sampleClass'] = sample_class
    metadata['R'] = r
    metadata['igocomplete'] = igocomplete
    metadata['libraryId'] = library.pop('libraryIgoId', None)
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


def update_sample_job(sample_id, igocomplete, request_id, request_metadata):
    logger.info(
        "Searching for job: %s for sample_id: %s" % (TYPES["UPDATE_SAMPLE_METADATA"], sample_id))
    job = Job(run=TYPES["UPDATE_SAMPLE_METADATA"],
              args={'sample_id': sample_id, 'igocomplete': igocomplete, 'request_id': request_id,
                    'request_metadata': request_metadata},
              status=JobStatus.CREATED, max_retry=1, children=[])
    job.save()
    return job
