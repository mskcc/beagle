import os
import copy
import logging
from django.conf import settings
from beagle_etl.jobs import TYPES
from notifier.models import JobGroup
from notifier.events import ETLSetRecipeEvent, OperatorRequestEvent, SetCIReviewEvent, SetLabelEvent, \
    NotForCIReviewEvent, UnknownAssayEvent, DisabledAssayEvent, AdminHoldEvent, CustomCaptureCCEvent
from notifier.tasks import send_notification, notifier_start
from beagle_etl.models import JobStatus, Job, Operator, Assay
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.repository.file_repository import FileRepository
from file_system.models import File, FileGroup, FileMetadata, FileType
from beagle_etl.exceptions import FailedToFetchSampleException, FailedToSubmitToOperatorException, \
    ErrorInconsistentDataException, MissingDataException, FailedToFetchPoolNormalException, FailedToCalculateChecksum
from runner.tasks import create_jobs_from_request
from file_system.helper.checksum import sha1, FailedToCalculateChecksum
from runner.operator.helper import format_sample_name
from beagle_etl.lims_client import LIMSClient

logger = logging.getLogger(__name__)


def fetch_new_requests_lims(timestamp):
    logger.info("Fetching requestIds")
    children = set()
    request_ids = LIMSClient.get_deliveries(timestamp)
    if not request_ids:
        logger.info("There is no new RequestIDs")
        return []
    for request in request_ids:
        job = create_request_job(request['request'])
        if job:
            if job.status == JobStatus.CREATED:
                children.add(str(job.id))
        else:
            logger.info("Job for requestId: %s not completed", request['request'])
    return list(children)


def create_request_job(request_id):
    logger.info(
        "Searching for job: %s for request_id: %s" % (TYPES['REQUEST'], request_id))
    count = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id,
                               status__in=[JobStatus.CREATED, JobStatus.IN_PROGRESS,
                                           JobStatus.WAITING_FOR_CHILDREN]).count()
    redelivery = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id,
                                    status=JobStatus.COMPLETED).count() > 0
    if count == 0:
        job_group = JobGroup()
        job_group.save()
        notifier_start(job_group, request_id)
        job = Job(run=TYPES['REQUEST'],
                  args={'request_id': request_id, 'job_group': str(job_group.id), 'redelivery': redelivery},
                  status=JobStatus.CREATED,
                  max_retry=1,
                  children=[],
                  callback=TYPES['REQUEST_CALLBACK'],
                  callback_args={'request_id': request_id, 'job_group': str(job_group.id)},
                  job_group=job_group)
        job.save()
        return job


def request_callback(request_id, job_group=None):
    jg = None
    try:
        jg = JobGroup.objects.get(id=job_group)
        logger.debug("[RequestCallback] JobGroup id: %s", job_group)
    except JobGroup.DoesNotExist:
        logger.debug("[RequestCallback] JobGroup not set")
    job_group_id = str(jg.id) if jg else None
    assays = Assay.objects.first()
    recipes = list(FileRepository.filter(metadata={'requestId': request_id}, values_metadata='recipe').all())
    if not recipes:
        raise FailedToSubmitToOperatorException(
           "Not enough metadata to choose the operator for requestId:%s" % request_id)

    if not all(item in assays.all for item in recipes):
        ci_review_e = SetCIReviewEvent(job_group_id).to_dict()
        send_notification.delay(ci_review_e)
        set_unknown_assay_label = SetLabelEvent(job_group_id, 'unrecognized_assay').to_dict()
        send_notification.delay(set_unknown_assay_label)
        unknown_assay_event = UnknownAssayEvent(job_group_id, recipes[0]).to_dict()
        send_notification.delay(unknown_assay_event)
        return []

    if any(item in assays.hold for item in recipes):
        admin_hold_event = AdminHoldEvent(job_group_id).to_dict()
        send_notification.delay(admin_hold_event)
        custom_capture_event = CustomCaptureCCEvent(job_group_id, recipes[0]).to_dict()
        send_notification.delay(custom_capture_event)
        return []

    if any(item in assays.disabled for item in recipes):
        not_for_ci = NotForCIReviewEvent(job_group_id).to_dict()
        send_notification.delay(not_for_ci)
        disabled_assay_event = DisabledAssayEvent(job_group_id, recipes[0]).to_dict()
        send_notification.delay(disabled_assay_event)
        return []

    operators = Operator.objects.filter(recipes__overlap=recipes)

    if not operators:
        msg = "No operator defined for requestId %s with recipe %s" % (request_id, recipes)
        logger.error(msg)
        e = OperatorRequestEvent(job_group_id, "[CIReviewEvent] %s" % msg).to_dict()
        send_notification.delay(e)
        ci_review_e = SetCIReviewEvent(job_group_id).to_dict()
        send_notification.delay(ci_review_e)
        raise FailedToSubmitToOperatorException(msg)
    for operator in operators:
        if not operator.active:
            msg = "Operator not active: %s" % operator.class_name
            logger.info(msg)
            e = OperatorRequestEvent(job_group_id, "[CIReviewEvent] %s" % msg).to_dict()
            send_notification.delay(e)
            error_label = SetLabelEvent(job_group_id, 'operator_inactive').to_dict()
            send_notification.delay(error_label)
            ci_review_e = SetCIReviewEvent(job_group_id).to_dict()
            send_notification.delay(ci_review_e)
        else:
            logger.info("Submitting request_id %s to %s operator" % (request_id, operator.class_name))
            create_jobs_from_request.delay(request_id, operator.id, job_group_id)
    return []


def fetch_samples(request_id, import_pooled_normals=True, import_samples=True, job_group=None, redelivery=False):
    logger.info("Fetching sampleIds for requestId:%s" % request_id)
    jg = None
    try:
        jg = JobGroup.objects.get(id=job_group)
        logger.debug("JobGroup found")
    except JobGroup.DoesNotExist:
        logger.debug("No JobGroup Found")
    children = set()
    sample_ids = LIMSClient.get_request_samples(request_id)
    if sample_ids['requestId'] != request_id:
        raise ErrorInconsistentDataException(
            "LIMS returned wrong response for request %s. Got %s instead" % (request_id, sample_ids['requestId']))
    request_metadata = {
        "dataAnalystEmail": sample_ids['dataAnalystEmail'],
        "dataAnalystName": sample_ids['dataAnalystName'],
        "investigatorEmail": sample_ids['investigatorEmail'],
        "investigatorName": sample_ids['investigatorName'],
        "labHeadEmail": sample_ids['labHeadEmail'],
        "labHeadName": sample_ids['labHeadName'],
        "otherContactEmails": sample_ids['otherContactEmails'],
        "dataAccessEmails": sample_ids['dataAccessEmails'],
        "qcAccessEmails": sample_ids['qcAccessEmails'],
        "projectManagerName": sample_ids['projectManagerName'],
        "recipe": sample_ids['recipe'],
        "piEmail": sample_ids["piEmail"],
    }
    set_recipe_event = ETLSetRecipeEvent(job_group, request_metadata['recipe']).to_dict()
    send_notification.delay(set_recipe_event)
    pooled_normals = sample_ids.get("pooledNormals", [])
    if import_pooled_normals and pooled_normals:
        for f in pooled_normals:
            job = get_or_create_pooled_normal_job(f, jg)
            children.add(str(job.id))
    if import_samples:
        if not sample_ids.get('samples', False):
            raise FailedToFetchSampleException("No samples reported for requestId: %s" % request_id)

        for sample in sample_ids.get('samples', []):
            job = create_sample_job(sample['igoSampleId'],
                                    sample['igocomplete'],
                                    request_id,
                                    request_metadata,
                                    redelivery,
                                    jg)
            children.add(str(job.id))
    return list(children)


def get_or_create_pooled_normal_job(filepath, job_group=None):
    logger.info(
        "Searching for job: %s for filepath: %s" % (TYPES['POOLED_NORMAL'], filepath))

    job = Job.objects.filter(run=TYPES['POOLED_NORMAL'], args__filepath=filepath).first()

    if not job:
        job = Job(run=TYPES['POOLED_NORMAL'],
                  args={'filepath': filepath, 'file_group_id': str(settings.POOLED_NORMAL_FILE_GROUP)},
                  status=JobStatus.CREATED,
                  max_retry=1,
                  children=[],
                  job_group=job_group)
        job.save()
    return job


def create_sample_job(sample_id, igocomplete, request_id, request_metadata, redelivery=False, job_group=None):
    job = Job(run=TYPES['SAMPLE'],
              args={'sample_id': sample_id, 'igocomplete': igocomplete, 'request_id': request_id,
                    'request_metadata': request_metadata, 'redelivery': redelivery},
              status=JobStatus.CREATED,
              max_retry=1, children=[],
              job_group=job_group)
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
        return output
    else:
        return string


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
    # if FileRepository.filter(path=filepath):
    try:
        File.objects.get(path=filepath)
    except File.DoesNotExist:
        logger.info("Pooled normal already created filepath")
    file_group_obj = FileGroup.objects.get(id=file_group_id)
    file_type_obj = FileType.objects.filter(name='fastq').first()
    assays = Assay.objects.first()
    assay_list = assays.all
    run_id = None
    preservation_type = None
    recipe = None
    try:
        parts = filepath.split('/')
        run_id = get_run_id_from_string(parts[6])
        pooled_normal_folder = parts[8]
        preservation_type = pooled_normal_folder
        preservation_type = preservation_type.split('Sample_')[1]
        preservation_type = preservation_type.split('POOLEDNORMAL')[0]
        potential_recipe = list(filter(lambda single_assay: single_assay in pooled_normal_folder, assay_list))
        if potential_recipe:
            potential_recipe.sort(key=len, reverse=True)
            recipe = potential_recipe[0]
    except Exception as e:
        raise FailedToFetchPoolNormalException("Failed to parse metadata for pooled normal file %s" % filepath)
    if preservation_type not in ('FFPE', 'FROZEN', 'MOUSE'):
        logger.info("Invalid preservation type %s" % preservation_type)
        return
    if recipe in assays.disabled:
        logger.info("Recipe %s, is marked as disabled" % recipe)
        return
    if None in [run_id, preservation_type, recipe]:
        logger.info("Invalid metadata runId:%s preservation:%s recipe:%s" % (run_id, preservation_type, recipe))
        return
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
        logger.info("File already exist %s." % (filepath))


def fetch_sample_metadata(sample_id, igocomplete, request_id, request_metadata, redelivery=False):
    logger.info("Fetch sample metadata for sampleId:%s" % sample_id)
    sampleMetadata = LIMSClient.get_sample_manifest(sample_id)
    try:
        data = sampleMetadata[0]
    except Exception as e:
        raise FailedToFetchSampleException(
            "Failed to fetch SampleManifest for sampleId:%s. Invalid response" % sample_id)
    if data['igoId'] != sample_id:
        # logger.info(data)
        logger.info("Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))
        raise FailedToFetchSampleException(
            "Failed to fetch SampleManifest for sampleId:%s. LIMS returned %s " % (sample_id, data['igoId']))

    validate_sample(sample_id, data.get('libraries'), igocomplete, redelivery)

    libraries = data.pop('libraries')
    for library in libraries:
        logger.info("Processing library %s" % library)
        runs = library.pop('runs')
        run_dict = convert_to_dict(runs)
        logger.info("Processing runs %s" % run_dict)
        for run in run_dict.values():
            logger.info("Processing run %s" % run)
            fastqs = run.pop('fastqs')
            for fastq in fastqs:
                logger.info("Adding file %s" % fastq)
                create_or_update_file(fastq, request_id, settings.IMPORT_FILE_GROUP, 'fastq', igocomplete, data,
                                      library, run,
                                      request_metadata, R1_or_R2(fastq), redelivery)


def validate_sample(sample_id, libraries, igocomplete, redelivery=False):
    conflict = False
    missing_fastq = False
    invalid_number_of_fastq = False
    failed_runs = []
    conflict_files = []
    if not libraries:
        if igocomplete:
            raise ErrorInconsistentDataException(
                "Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id)
        else:
            raise MissingDataException("Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id)
    for library in libraries:
        runs = library.get('runs')
        if not runs:
            logger.error("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
            if igocomplete:
                raise ErrorInconsistentDataException(
                    "Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
            else:
                raise MissingDataException(
                    "Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
        run_dict = convert_to_dict(runs)
        for run in run_dict.values():
            fastqs = run.get('fastqs')
            if not fastqs:
                logger.error("Failed to fetch SampleManifest for sampleId:%s. Fastqs empty" % sample_id)
                missing_fastq = True
                failed_runs.append(run['runId'])
            else:
                if not redelivery:
                    for fastq in fastqs:
                        file_search = None
                        try:
                            file_search = File.objects.get(path=fastq)
                        except File.DoesNotExist:
                            pass
                        # file_search = FileRepository.filter(path=fastq).first()
                        logger.info("Processing %s" % fastq)
                        if file_search:
                            msg = "File %s already created with id:%s" % (file_search.path, str(file_search.id))
                            logger.error(msg)
                            conflict = True
                            conflict_files.append((file_search.path, str(file_search.id)))
    if missing_fastq:
        if igocomplete:
            raise ErrorInconsistentDataException(
                "Missing fastq files for igcomplete: %s sample %s : %s" % (
                igocomplete, sample_id, ' '.join(failed_runs)))
        else:
            raise MissingDataException(
                "Missing fastq files for igcomplete: %s sample %s : %s" % (
                    igocomplete, sample_id, ' '.join(failed_runs)))
    if not redelivery:
        if conflict:
            res_str = ""
            for f in conflict_files:
                res_str += "%s: %s" % (f[0], f[1])
            raise ErrorInconsistentDataException(
                "Conflict of fastq file(s) %s" % res_str)


def R1_or_R2(filename):
    reversed_filename = ''.join(reversed(filename))
    R1_idx = reversed_filename.find('1R')
    R2_idx = reversed_filename.find('2R')
    if R1_idx == -1 and R2_idx == -1:
        return "UNKNOWN"
    elif R1_idx > 0 and R2_idx == -1:
        return "R1"
    elif R2_idx > 0 and R1_idx == -1:
        return 'R2'
    elif R1_idx > 0 and R2_idx > 0:
        if R1_idx < R2_idx:
            return 'R1'
        else:
            return 'R2'
    return 'UNKNOWN'


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
                    raise FailedToFetchSampleException(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][0], run['fastqs'][0]))
                if run_dict[run['runId']]['fastqs'][1] != run['fastqs'][1]:
                    logger.error(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][1], run['fastqs'][1]))
                    raise FailedToFetchSampleException(
                        "File %s do not match with %s" % (run_dict[run['runId']]['fastqs'][1], run['fastqs'][1]))
    return run_dict


def create_or_update_file(path, request_id, file_group_id, file_type, igocomplete, data, library, run, request_metadata, r, update=False):
    logger.info("Creating file %s " % path)
    try:
        file_group_obj = FileGroup.objects.get(id=file_group_id)
        file_type_obj = FileType.objects.filter(name=file_type).first()
        metadata = copy.deepcopy(data)
        library_copy = copy.deepcopy(library)
        sample_name = metadata.pop('cmoSampleName', None)
        external_sample_name = metadata.pop('sampleName', None)
        sample_id = metadata.pop('igoId', None)
        patient_id = metadata.pop('cmoPatientId', None)
        sample_class = metadata.pop('cmoSampleClass', None)
        specimen_type = metadata.pop('specimenType', None)
        metadata['specimenType'] = specimen_type
        metadata['requestId'] = request_id
        metadata['sampleName'] = sample_name
        metadata['cmoSampleName'] = format_sample_name(sample_name, specimen_type)
        metadata['externalSampleId'] = external_sample_name
        metadata['sampleId'] = sample_id
        metadata['patientId'] = patient_id
        metadata['sampleClass'] = sample_class
        metadata['R'] = r
        metadata['igocomplete'] = igocomplete
        metadata['sequencingCenter'] = 'MSKCC'
        metadata['platform'] = 'Illumina'
        metadata['libraryId'] = library_copy.pop('libraryIgoId', None)
        for k, v in library_copy.items():
            metadata[k] = v
        for k, v in run.items():
            metadata[k] = v
        for k, v in request_metadata.items():
            metadata[k] = v
        # validator = MetadataValidator(METADATA_SCHEMA)
    except Exception as e:
        logger.error("Failed to parse metadata for file %s path" % path)
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    try:
        logger.info(metadata)
        # validator.validate(metadata)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        try:
            f = File.objects.get(path=path)
        except File.DoesNotExist:
            create_file_object(path, file_group_obj, metadata, file_type_obj)
        else:
            if update:
                update_file_object(f, path, metadata)
            else:
                raise FailedToFetchSampleException("File %s already exist with id %s" % (path, str(f.id)))


def create_file_object(path, file_group, metadata, file_type):
    try:
        f = File.objects.create(file_name=os.path.basename(path), path=path, file_group=file_group,
                                file_type=file_type)
        f.save()
        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
        Job.objects.create(run=TYPES["CALCULATE_CHECKSUM"],
                           args={'file_id': str(f.id), 'path': path},
                           status=JobStatus.CREATED, max_retry=3, children=[])
    except Exception as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))


def update_file_object(file_object, path, metadata):
    data = {
        "path": path,
        "metadata": metadata
    }
    serializer = UpdateFileSerializer(file_object, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        logger.error("Failed to update file %s: Error %s" % (path, serializer.errors))
        raise FailedToFetchSampleException(
            "Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors))


def calculate_checksum(file_id, path):
    try:
        checksum = sha1(path)
    except FailedToCalculateChecksum as e:
        logger.info("Failed to calculate checksum for file: %s: %s", file_id, path)
        raise FailedToCalculateChecksum("Failed to calculate checksum. Error: File %s not found", file_id)
    try:
        f = File.objects.get(id=file_id)
        f.checksum = checksum
        f.save(update_fields=["checksum"])
    except File.DoesNotExist:
        logger.info("Failed to calculate checksum. Error: File %s not found", file_id)
        raise FailedToCalculateChecksum("Failed to calculate checksum. Error: File %s not found", file_id)
    return []
