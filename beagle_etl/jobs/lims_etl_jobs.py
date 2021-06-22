import os
import copy
import logging
import asyncio
from deepdiff import DeepDiff
from django.conf import settings
from beagle_etl.jobs import TYPES
from notifier.models import JobGroup, JobGroupNotifier
from notifier.events import ETLSetRecipeEvent, OperatorRequestEvent, SetCIReviewEvent, SetLabelEvent, \
    NotForCIReviewEvent, UnknownAssayEvent, DisabledAssayEvent, AdminHoldEvent, CustomCaptureCCEvent, RedeliveryEvent, \
    RedeliveryUpdateEvent, ETLImportCompleteEvent, ETLImportPartiallyCompleteEvent, \
    ETLImportNoSamplesEvent, LocalStoreFileEvent, ExternalEmailEvent, OnlyNormalSamplesEvent, WESJobFailedEvent

from notifier.tasks import send_notification, notifier_start
from beagle_etl.models import JobStatus, Job, Operator, ETLConfiguration
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.repository.file_repository import FileRepository
from file_system.models import File, FileGroup, FileMetadata, FileType, ImportMetadata, Sample
from beagle_etl.exceptions import FailedToFetchSampleException, FailedToSubmitToOperatorException, \
    ErrorInconsistentDataException, MissingDataException, FailedToFetchPoolNormalException, FailedToCalculateChecksum, FailedToCopyFilePermissionDeniedException, FailedToCopyFileException
from runner.tasks import create_jobs_from_request
from file_system.helper.checksum import sha1, FailedToCalculateChecksum
from runner.operator.helper import format_sample_name, format_patient_id
from beagle_etl.lims_client import LIMSClient
from beagle_etl.copy_service import CopyService
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


def parse_new_request_job(request):
    request_id = request['requestId']
    logger.info(
        "Searching for job: %s for request_id: %s" % (TYPES['REQUEST'], request_id))
    count = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id,
                               status__in=[JobStatus.CREATED, JobStatus.IN_PROGRESS,
                                           JobStatus.WAITING_FOR_CHILDREN]).count()
    request_redelivered = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id).count() > 0

    assays = ETLConfiguration.objects.first()

    if request_redelivered and not assays.redelivery:
        return None, "Request is redelivered, but redelivery deactivated"

    if count == 0:
        job_group = JobGroup()
        job_group.save()
        job_group_notifier_id = notifier_start(job_group, request_id)
        job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)
        job = Job(run=TYPES['PARSE_SAMPLE_JOB'],
                  args={'request': request, 'job_group': str(job_group.id),
                        'job_group_notifier': str(job_group_notifier.id), 'redelivery': request_redelivered},
                  status=JobStatus.CREATED,
                  max_retry=1,
                  children=[],
                  callback=TYPES['REQUEST_CALLBACK'],
                  callback_args={'request_id': request_id,
                                 'recipe': request['recipe'],
                                 'job_group': str(job_group.id),
                                 'job_group_notifier': job_group_notifier_id},
                  job_group=job_group,
                  job_group_notifier=job_group_notifier)
        job.save()
        if request_redelivered:
            redelivery_event = RedeliveryEvent(job_group_notifier_id).to_dict()
            send_notification.delay(redelivery_event)
        return [str(job.id)]


def request_callback(request_id, recipe, job_group=None, job_group_notifier=None):
    jg = None
    jgn = None
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier)
        logger.debug("[RequestCallback] JobGroup id: %s", job_group)
    except JobGroupNotifier.DoesNotExist:
        logger.debug("[RequestCallback] JobGroup not set")
    job_group_notifier_id = str(jgn.id) if jgn else None
    assays = ETLConfiguration.objects.first()

    if not all([JobStatus(job['status']) == JobStatus.COMPLETED for job in
                Job.objects.filter(job_group=job_group, run=TYPES['SAMPLE'], args__igocomplete=True).values(
                    "status")]) and recipe in settings.WES_ASSAYS:
        wes_job_failed = WESJobFailedEvent(job_group_notifier_id, recipe)
        send_notification.delay(wes_job_failed.to_dict())

    if not recipe:
        raise FailedToSubmitToOperatorException(
           "Not enough metadata to choose the operator for requestId:%s" % request_id)

    if not all(item in assays.all_recipes for item in (recipe,)):
        ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(ci_review_e)
        set_unknown_assay_label = SetLabelEvent(job_group_notifier_id, 'unrecognized_assay').to_dict()
        send_notification.delay(set_unknown_assay_label)
        unknown_assay_event = UnknownAssayEvent(job_group_notifier_id, recipe).to_dict()
        send_notification.delay(unknown_assay_event)
        return []

    if any(item in assays.hold_recipes for item in (recipe,)):
        admin_hold_event = AdminHoldEvent(job_group_notifier_id).to_dict()
        send_notification.delay(admin_hold_event)
        custom_capture_event = CustomCaptureCCEvent(job_group_notifier_id, recipe).to_dict()
        send_notification.delay(custom_capture_event)
        return []

    if any(item in assays.disabled_recipes for item in [recipe,]):
        not_for_ci = NotForCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(not_for_ci)
        disabled_assay_event = DisabledAssayEvent(job_group_notifier_id, recipe).to_dict()
        send_notification.delay(disabled_assay_event)
        return []

    if len(FileRepository.filter(metadata={'requestId': request_id}, values_metadata='recipe').all()) == 0:
        no_samples_event = AdminHoldEvent(job_group_notifier_id).to_dict()
        send_notification.delay(no_samples_event)
        return []

    if not all([JobStatus(job['status']) == JobStatus.COMPLETED for job in
                Job.objects.filter(job_group=job_group).values("status")]):
        ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(ci_review_e)

    lab_head_email = FileRepository.filter(metadata={'requestId': request_id}, values_metadata='labHeadEmail').first()
    try:
        if lab_head_email.split("@")[1] != "mskcc.org":
            event = ExternalEmailEvent(job_group_notifier_id, request_id).to_dict()
            send_notification.delay(event)
    except Exception:
        logger.error("Failed to check labHeadEmail")

    if len(FileRepository.filter(metadata={'requestId': request_id, 'tumorOrNormal': 'Tumor'})) == 0:
        only_normal_samples_event = OnlyNormalSamplesEvent(job_group_notifier_id, request_id).to_dict()
        send_notification.delay(only_normal_samples_event)
        if recipe in settings.ASSAYS_ADMIN_HOLD_ONLY_NORMALS:
            admin_hold_event = AdminHoldEvent(job_group_notifier_id).to_dict()
            send_notification.delay(admin_hold_event)
            return []

    operators = Operator.objects.filter(recipes__overlap=[recipe])

    if not operators:
        # TODO: Import ticket will have CIReviewNeeded
        msg = "No operator defined for requestId %s with recipe %s" % (request_id, recipe)
        logger.error(msg)
        e = OperatorRequestEvent(job_group_notifier_id, "[CIReviewEvent] %s" % msg).to_dict()
        send_notification.delay(e)
        ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(ci_review_e)
        raise FailedToSubmitToOperatorException(msg)
    for operator in operators:
        if not operator.active:
            msg = "Operator not active: %s" % operator.class_name
            logger.info(msg)
            e = OperatorRequestEvent(job_group_notifier_id, "[CIReviewEvent] %s" % msg).to_dict()
            send_notification.delay(e)
            error_label = SetLabelEvent(job_group_notifier_id, 'operator_inactive').to_dict()
            send_notification.delay(error_label)
            ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
            send_notification.delay(ci_review_e)
        else:
            logger.info("Submitting request_id %s to %s operator" % (request_id, operator.class_name))
            if Job.objects.filter(job_group=job_group, args__request_id=request_id, run=TYPES['SAMPLE'],
                                  status=JobStatus.FAILED).all():
                partialy_complete_event = ETLImportPartiallyCompleteEvent(job_notifier=job_group_notifier_id).to_dict()
                send_notification.delay(partialy_complete_event)
            else:
                complete_event = ETLImportCompleteEvent(job_notifier=job_group_notifier_id).to_dict()
                send_notification.delay(complete_event)

            create_jobs_from_request.delay(request_id, operator.id, job_group)
    return []


def parse_samples_job(request, import_pooled_normals=True, import_samples=True, job_group=None,
                      job_group_notifier=None, redelivery=False):
    request_id = request['requestId']
    logger.info("Fetching sampleIds for requestId:%s" % request_id)
    jg = None
    jgn = None
    try:
        jg = JobGroup.objects.get(id=job_group)
        logger.debug("JobGroup found")
    except JobGroup.DoesNotExist:
        logger.debug("No JobGroup Found")
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier)
        logger.debug("JobGroup found")
    except JobGroupNotifier.DoesNotExist:
        logger.debug("No JobGroup Found")
    children = set()

    samples_list = request.pop('samples')
    sample_data = _convert_to_dict(request.pop('sampleManifestList'))
    print(sample_data)
    pooled_normals = request.pop('pooledNormals')
    request_metadata = request

    set_recipe_event = ETLSetRecipeEvent(job_group_notifier, request_metadata['recipe']).to_dict()
    send_notification.delay(set_recipe_event)

    if import_pooled_normals and pooled_normals:
        for f in pooled_normals:
            job = get_or_create_pooled_normal_job(f, jg, jgn, redelivery=redelivery)
            children.add(str(job.id))

    if import_samples:
        for sample in samples_list:
            job = create_parse_sample_job(sample_data[sample['igoSampleId']], sample['igocomplete'], request_metadata,
                                          redelivery, jg, jgn)
            children.add(str(job.id))
    return list(children)


def _convert_to_dict(sample_list):
    sample_dict = dict()
    for sample in sample_list:
        sample_dict[sample['igoId']] = sample
    return sample_dict


def get_or_create_pooled_normal_job(filepath, job_group=None, job_group_notifier=None, redelivery=False):
    logger.info(
        "Searching for job: %s for filepath: %s" % (TYPES['POOLED_NORMAL'], filepath))

    job = Job.objects.filter(run=TYPES['POOLED_NORMAL'], args__filepath=filepath).first()

    if not job or redelivery:
        job = Job.objects.create(run=TYPES['POOLED_NORMAL'],
                                 args={'filepath': filepath, 'file_group_id': str(settings.POOLED_NORMAL_FILE_GROUP)},
                                 status=JobStatus.CREATED,
                                 max_retry=1,
                                 children=[],
                                 job_group=job_group,
                                 job_group_notifier=job_group_notifier)
    return job


def create_parse_sample_job(sample_data, igocomplete, request_metadata, redelivery=False, job_group=None,
                            job_group_notifier=None):
    job = Job(run=TYPES['PARSE_SAMPLE_METADATA'],
              args={'sample_data': sample_data, 'igocomplete': igocomplete, 'request_metadata': request_metadata,
                    'redelivery': redelivery, 'job_group_notifier': str(job_group_notifier.id)},
              status=JobStatus.CREATED,
              max_retry=1, children=[],
              job_group=job_group,
              job_group_notifier=job_group_notifier)
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
    assays = ETLConfiguration.objects.first()
    assay_list = assays.all_recipes
    run_id = None
    preservation_type = None
    recipe = None
    try:
        parts = filepath.split('/')
        path_shift = 0
        # path_shift needed for /ifs/archive/GCL/hiseq/ -> /igo/delivery/ transition
        if 'igo' in parts[1]:
            path_shift = 2
        run_id = get_run_id_from_string(parts[6-path_shift])
        pooled_normal_folder = parts[8-path_shift]
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
    if recipe in assays.disabled_recipes:
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
        new_path = CopyService.remap(recipe, filepath)
        if new_path != filepath:
            CopyService.copy(filepath, new_path)
    except Exception as e:
        logger.error("Failed to copy file %s." % (filepath,))
        raise FailedToFetchPoolNormalException("Failed to copy file %s. Error %s" % (filepath, str(e)))

    try:
        f = File.objects.create(file_name=os.path.basename(filepath), path=filepath, file_group=file_group_obj,
                                file_type=file_type_obj)
        f.save()
        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
    except Exception as e:
        logger.info("File already exist %s." % (filepath))


def parse_sample_metadata(sample_data, igocomplete, request_metadata, redelivery=False, job_group_notifier=None):
    validate_sample(sample_data, sample_data.get('libraries', []), igocomplete, redelivery)
    libraries = sample_data.pop('libraries')
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
                create_or_update_file(fastq, request_metadata['requestId'], settings.IMPORT_FILE_GROUP, 'fastq',
                                      igocomplete, sample_data, library, run, request_metadata, R1_or_R2(fastq),
                                      update=redelivery, job_group_notifier=job_group_notifier)


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
                run_id = run['runId'] if run['runId'] else 'None'
                failed_runs.append(run_id)
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


def create_or_update_file(path, request_id, file_group_id, file_type, igocomplete, data, library, run,
                          request_metadata, r, update=False, job_group_notifier=None):
    logger.info("Creating file %s " % path)
    try:
        file_group_obj = FileGroup.objects.get(id=file_group_id)
        file_type_obj = FileType.objects.filter(name=file_type).first()
        lims_metadata = copy.deepcopy(data)
        library_copy = copy.deepcopy(library)
        lims_metadata['requestId'] = request_id
        lims_metadata['igocomplete'] = igocomplete
        lims_metadata['R'] = r
        for k, v in library_copy.items():
            lims_metadata[k] = v
        for k, v in run.items():
            lims_metadata[k] = v
        for k, v in request_metadata.items():
            lims_metadata[k] = v
        metadata = format_metadata(lims_metadata)
        # validator = MetadataValidator(METADATA_SCHEMA)
    except Exception as e:
        logger.error("Failed to parse metadata for file %s path" % path)
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    try:
        logger.info(lims_metadata)
        # validator.validate(metadata)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        recipe = metadata.get('recipe', '')
        new_path = CopyService.remap(recipe, path) # Get copied file path
        f = FileRepository.filter(path=new_path).first()
        if not f:
            try:
                if path != new_path:
                    CopyService.copy(path, new_path)
            except Exception as e:
                if "Permission denied" in str(e):
                    raise FailedToCopyFilePermissionDeniedException("Failed to copy file %s. Error %s" % (path, str(e)))
                else:
                    raise FailedToCopyFileException("Failed to copy file %s. Error %s" % (path, str(e)))
            create_file_object(new_path, file_group_obj, lims_metadata, metadata, file_type_obj)
            if update:
                message = "File registered: %s" % path
                update = RedeliveryUpdateEvent(job_group_notifier, message).to_dict()
                send_notification.delay(update)
        else:
            if update:
                before = f.file.filemetadata_set.order_by('-created_date').count()
                update_file_object(f.file, f.file.path, metadata)
                after = f.file.filemetadata_set.order_by('-created_date').count()
                if after != before:
                    all_metadata = f.file.filemetadata_set.order_by('-created_date')
                    ddiff = DeepDiff(all_metadata[1].metadata,
                                     all_metadata[0].metadata,
                                     ignore_order=True)
                    diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, all_metadata[0].version)
                    message = "Updating file metadata: %s, details in file %s\n" % (path, diff_file_name)
                    update = RedeliveryUpdateEvent(job_group_notifier, message).to_dict()
                    diff_details_event = LocalStoreFileEvent(job_group_notifier, diff_file_name, str(ddiff)).to_dict()
                    send_notification.delay(update)
                    send_notification.delay(diff_details_event)
            else:
                raise FailedToFetchSampleException("File %s already exist with id %s" % (path, str(f.id)))


def format_metadata(original_metadata):
    metadata = dict()
    original_metadata_copy = copy.deepcopy(original_metadata)
    sample_name = original_metadata_copy.pop('cmoSampleName', None)
    external_sample_name = original_metadata_copy.pop('sampleName', None)
    sample_id = original_metadata_copy.pop('igoId', None)
    patient_id = original_metadata_copy.pop('cmoPatientId', None)
    sample_class = original_metadata_copy.pop('cmoSampleClass', None)
    specimen_type = original_metadata_copy.pop('specimenType', None)
    # ciTag is the new field which needs to be used for the operators
    metadata['ciTag'] = format_sample_name(sample_name, specimen_type)
    metadata['cmoSampleName'] = format_sample_name(sample_name, specimen_type)
    metadata['specimenType'] = specimen_type
    metadata['sampleName'] = sample_name
    metadata['externalSampleId'] = external_sample_name
    metadata['sampleId'] = sample_id
    metadata['patientId'] = format_patient_id(patient_id)
    metadata['sampleClass'] = sample_class
    metadata['sequencingCenter'] = 'MSKCC'
    metadata['platform'] = 'Illumina'
    metadata['libraryId'] = original_metadata_copy.pop('libraryIgoId', None)
    for k, v in original_metadata_copy.items():
        metadata[k] = v
    return metadata


def create_file_object(path, file_group, lims_metadata, metadata, file_type):
    try:
        f = File.objects.create(file_name=os.path.basename(path), path=path, file_group=file_group,
                                file_type=file_type)
        f.save()

        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
        Job.objects.create(run=TYPES["CALCULATE_CHECKSUM"],
                           args={'file_id': str(f.id), 'path': path},
                           status=JobStatus.CREATED, max_retry=3, children=[])
        import_metadata = ImportMetadata.objects.create(file=f, metadata=lims_metadata)
    except Exception as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))


def update_file_object(file_object, path, metadata):
    data = {
        "path": path,
        "metadata": metadata,
    }
    try:
        user = User.objects.get(username=settings.ETL_USER)
        data['user'] = user.id
    except User.DoesNotExist:
        user = None
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
