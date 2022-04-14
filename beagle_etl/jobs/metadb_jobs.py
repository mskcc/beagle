import os
import copy
import json
import logging
from deepdiff import DeepDiff
from datetime import datetime
from celery import shared_task
from django.conf import settings
from beagle_etl.jobs import TYPES
from notifier.models import JobGroup, JobGroupNotifier
from notifier.events import (
    ETLSetRecipeEvent,
    OperatorRequestEvent,
    SetCIReviewEvent,
    SetLabelEvent,
    NotForCIReviewEvent,
    UnknownAssayEvent,
    DisabledAssayEvent,
    AdminHoldEvent,
    CustomCaptureCCEvent,
    RedeliveryEvent,
    RedeliveryUpdateEvent,
    ETLImportCompleteEvent,
    ETLImportPartiallyCompleteEvent,
    LocalStoreFileEvent,
    ExternalEmailEvent,
    OnlyNormalSamplesEvent,
    WESJobFailedEvent,
    ETLImportEvent,
    ETLJobsLinksEvent,
)
from notifier.tasks import send_notification, notifier_start
from beagle_etl.exceptions import ETLExceptions
from beagle_etl.models import JobStatus, Job, Operator, ETLConfiguration
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.repository.file_repository import FileRepository
from file_system.models import File, FileGroup, FileMetadata, FileType, ImportMetadata, Sample, Request, Patient
from beagle_etl.exceptions import (
    FailedToFetchSampleException,
    FailedToSubmitToOperatorException,
    ErrorInconsistentDataException,
    MissingDataException,
    FailedToFetchPoolNormalException,
    FailedToCalculateChecksum,
    FailedToCopyFilePermissionDeniedException,
    FailedToCopyFileException,
)
from runner.tasks import create_jobs_from_request
from file_system.helper.checksum import sha1, FailedToCalculateChecksum
from runner.operator.helper import format_sample_name, format_patient_id
from beagle_etl.copy_service import CopyService
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


@shared_task
def new_request(input_data):
    data = json.loads(input_data)
    request_id = data.get(settings.REQUEST_ID_METADATA_KEY)
    if data.get("deliveryDate"):
        delivery_date = datetime.fromtimestamp(data["deliveryDate"] / 1000)
    else:
        delivery_date = datetime.now()
    try:
        request = Request.objects.get(request_id=request_id)
        request.delivery_date = delivery_date
        request.save()
    except Request.DoesNotExist:
        Request.objects.create(request_id=request_id, delivery_date=delivery_date)

    logger.info("Importing new request: %s" % request_id)

    sample_jobs = []

    igocomplete = True
    """
    Fix until igoComplete is in the MetaDB
    """
    samples = data.get("samples")
    for idx, sample in enumerate(data.get("sampleManifestList", [])):
        igocomplete = samples[idx]["igocomplete"]
        try:
            validate_sample(sample, sample.get("libraries", []), igocomplete)
            sample_status = {
                "type": "SAMPLE",
                "igocomplete": igocomplete,
                "sample": sample["primaryId"],
                "status": "COMPLETED",
                "message": "",
                "code": None,
            }
            sample_jobs.append(sample_status)
        except Exception as e:
            if isinstance(e, ETLExceptions):
                sample_status = {
                    "type": "SAMPLE",
                    "igocomplete": igocomplete,
                    "sample": sample["primaryId"],
                    "status": "FAILED",
                    "message": str(e),
                    "code": e.code,
                }
            else:
                sample_status = {
                    "type": "SAMPLE",
                    "igocomplete": igocomplete,
                    "sample": sample["primaryId"],
                    "status": "FAILED",
                    "message": str(e),
                    "code": None,
                }
            sample_jobs.append(sample_status)

    job_group = JobGroup()
    job_group.save()
    job_group_notifier_id = notifier_start(job_group, request_id)
    job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)

    project_id = data.get(settings.PROJECT_ID_METADATA_KEY)
    recipe = data.get(settings.RECIPE_METADATA_KEY)

    set_recipe_event = ETLSetRecipeEvent(str(job_group_notifier.id), recipe).to_dict()
    send_notification.delay(set_recipe_event)

    project_manager_name = data.get("projectManagerName")
    pi_email = data.get("piEmail")
    lab_head_name = data.get("labHeadName")
    lab_head_email = data.get("labHeadEmail")
    investigator_name = data.get("investigatorName")
    investigator_email = data.get("investigatorEmail")
    data_analyst_name = data.get("dataAnalystName")
    data_analyst_email = data.get("dataAnalystEmail")
    other_contact_emails = data.get("otherContactEmails")
    data_access_email = data.get("dataAccessEmails")
    qc_access_email = data.get("qcAccessEmails")

    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: request_id,
        settings.PROJECT_ID_METADATA_KEY: project_id,
        settings.RECIPE_METADATA_KEY: recipe,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        "labHeadName": lab_head_name,
        "labHeadEmail": lab_head_email,
        "investigatorName": investigator_name,
        "investigatorEmail": investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }

    samples = data.get("samples")
    for idx, sample in enumerate(data.get("samples")):
        sample_id = sample["primaryId"]
        logger.info("Parsing sample: %s" % sample_id)
        libraries = sample.pop("libraries")
        for library in libraries:
            logger.info("Processing library %s" % library)
            runs = library.pop("runs")
            for run in runs:
                logger.info("Processing run %s" % run)
                fastqs = run.pop("fastqs")
                for fastq in fastqs:
                    logger.info("Adding file %s" % fastq)
                    try:
                        create_or_update_file(
                            fastq,
                            request_id,
                            settings.IMPORT_FILE_GROUP,
                            "fastq",
                            igocomplete,
                            sample,
                            library,
                            run,
                            request_metadata,
                            R1_or_R2(fastq),
                        )
                    except Exception as e:
                        logger.error(e)
    pooled_normal = data.get("pooledNormals", [])
    pooled_normal_jobs = []
    for pn in pooled_normal:
        try:
            create_pooled_normal(pn, str(settings.POOLED_NORMAL_FILE_GROUP))
        except Exception as e:
            pooled_normal_jobs.append(
                {"type": "POOLED_NORMAL", "sample": "", "status": "FAILED", "message": str(e), "code": None}
            )
        else:
            pooled_normal_jobs.append(
                {"type": "POOLED_NORMAL", "sample": "", "status": "COMPLETED", "message": pn, "code": None}
            )

    _generate_ticket_description(
        request_id, str(job_group.id), job_group_notifier_id, sample_jobs, pooled_normal_jobs, request_metadata
    )

    request_callback(request_id, recipe, sample_jobs, job_group, job_group_notifier)


def request_callback(request_id, recipe, sample_jobs, job_group=None, job_group_notifier=None):
    """
    :param request_id: 08944_B
    :param recipe: IMPACT438
    :param sample_jobs: sample_jobs[]
    :param job_group: JobGroup instance
    :param job_group_notifier: JobGroupNotifier instance
    :return:
    """
    assays = ETLConfiguration.objects.first()

    if recipe in settings.WES_ASSAYS:
        for job in sample_jobs:
            if job["igocomplete"] and job["status"] != "COMPLETED":
                wes_job_failed = WESJobFailedEvent(str(job_group_notifier.id), recipe)
                send_notification.delay(wes_job_failed.to_dict())

    if not recipe:
        raise FailedToSubmitToOperatorException(
            "Not enough metadata to choose the operator for requestId:%s" % request_id
        )

    if not all(item in assays.all_recipes for item in (recipe,)):
        ci_review_e = SetCIReviewEvent(str(job_group_notifier.id)).to_dict()
        send_notification.delay(ci_review_e)
        set_unknown_assay_label = SetLabelEvent(str(job_group_notifier.id), "unrecognized_assay").to_dict()
        send_notification.delay(set_unknown_assay_label)
        unknown_assay_event = UnknownAssayEvent(str(job_group_notifier.id), recipe).to_dict()
        send_notification.delay(unknown_assay_event)
        return []

    if any(item in assays.hold_recipes for item in (recipe,)):
        admin_hold_event = AdminHoldEvent(str(job_group_notifier.id)).to_dict()
        send_notification.delay(admin_hold_event)
        custom_capture_event = CustomCaptureCCEvent(str(job_group_notifier.id), recipe).to_dict()
        send_notification.delay(custom_capture_event)
        return []

    if any(
        item in assays.disabled_recipes
        for item in [
            recipe,
        ]
    ):
        not_for_ci = NotForCIReviewEvent(str(job_group_notifier.id)).to_dict()
        send_notification.delay(not_for_ci)
        disabled_assay_event = DisabledAssayEvent(str(job_group_notifier.id), recipe).to_dict()
        send_notification.delay(disabled_assay_event)
        return []

    if (
        len(
            FileRepository.filter(
                metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.RECIPE_METADATA_KEY
            ).all()
        )
        == 0
    ):
        no_samples_event = AdminHoldEvent(str(job_group_notifier.id)).to_dict()
        send_notification.delay(no_samples_event)
        return []

    for job in sample_jobs:
        if job["igocomplete"] and job["status"] != "COMPLETED":
            ci_review_e = SetCIReviewEvent(str(job_group_notifier.id)).to_dict()
            send_notification.delay(ci_review_e)

    lab_head_email = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata="labHeadEmail"
    ).first()
    try:
        if lab_head_email.split("@")[1] != "mskcc.org":
            event = ExternalEmailEvent(str(job_group_notifier.id), request_id).to_dict()
            send_notification.delay(event)
    except Exception:
        logger.error("Failed to check labHeadEmail")

    if (
        len(FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id, "tumorOrNormal": "Tumor"}))
        == 0
    ):
        only_normal_samples_event = OnlyNormalSamplesEvent(str(job_group_notifier.id), request_id).to_dict()
        send_notification.delay(only_normal_samples_event)
        if recipe in settings.ASSAYS_ADMIN_HOLD_ONLY_NORMALS:
            admin_hold_event = AdminHoldEvent(str(job_group_notifier.id)).to_dict()
            send_notification.delay(admin_hold_event)
            return []

    operators = Operator.objects.filter(recipes__overlap=[recipe])

    if not operators:
        # TODO: Import ticket will have CIReviewNeeded
        msg = "No operator defined for requestId %s with recipe %s" % (request_id, recipe)
        logger.error(msg)
        e = OperatorRequestEvent(str(job_group_notifier.id), "[CIReviewEvent] %s" % msg).to_dict()
        send_notification.delay(e)
        ci_review_e = SetCIReviewEvent(str(job_group_notifier.id)).to_dict()
        send_notification.delay(ci_review_e)
        raise FailedToSubmitToOperatorException(msg)
    for operator in operators:
        if not operator.active:
            msg = "Operator not active: %s" % operator.class_name
            logger.info(msg)
            e = OperatorRequestEvent(str(job_group_notifier.id), "[CIReviewEvent] %s" % msg).to_dict()
            send_notification.delay(e)
            error_label = SetLabelEvent(str(job_group_notifier.id), "operator_inactive").to_dict()
            send_notification.delay(error_label)
            ci_review_e = SetCIReviewEvent(str(job_group_notifier.id)).to_dict()
            send_notification.delay(ci_review_e)
        else:
            logger.info("Submitting request_id %s to %s operator" % (request_id, operator.class_name))
            if Job.objects.filter(
                job_group=job_group, args__request_id=request_id, run=TYPES["SAMPLE"], status=JobStatus.FAILED
            ).all():
                partialy_complete_event = ETLImportPartiallyCompleteEvent(
                    job_notifier=str(job_group_notifier.id)
                ).to_dict()
                send_notification.delay(partialy_complete_event)
            else:
                complete_event = ETLImportCompleteEvent(job_notifier=str(job_group_notifier.id)).to_dict()
                send_notification.delay(complete_event)

            create_jobs_from_request.delay(request_id, operator.id, str(job_group.id))
    return []


@shared_task
def update_request_job(input_data):
    data = json.loads(input_data)
    request_id = data.get(settings.REQUEST_ID_METADATA_KEY)
    files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id})

    project_id = data.get(settings.PROJECT_ID_METADATA_KEY)
    recipe = data.get(settings.RECIPE_METADATA_KEY)

    job_group = JobGroup()
    job_group.save()
    job_group_notifier_id = notifier_start(job_group, request_id)
    job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)

    redelivery_event = RedeliveryEvent(job_group_notifier_id).to_dict()
    send_notification.delay(redelivery_event)

    project_manager_name = data.get("projectManagerName")
    pi_email = data.get("piEmail")
    lab_head_name = data.get("labHeadName")
    lab_head_email = data.get("labHeadEmail")
    investigator_name = data.get("investigatorName")
    investigator_email = data.get("investigatorEmail")
    data_analyst_name = data.get("dataAnalystName")
    data_analyst_email = data.get("dataAnalystEmail")
    other_contact_emails = data.get("otherContactEmails")
    data_access_email = data.get("dataAccessEmails")
    qc_access_email = data.get("qcAccessEmails")

    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: request_id,
        settings.PROJECT_ID_METADATA_KEY: project_id,
        settings.RECIPE_METADATA_KEY: recipe,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        "labHeadName": lab_head_name,
        "labHeadEmail": lab_head_email,
        "investigatorName": investigator_name,
        "investigatorEmail": investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }

    samples = list()
    sample_status_list = list()
    for f in files:
        new_metadata = f.metadata
        new_metadata.update(request_metadata)
        if f.metadata[settings.SAMPLE_ID_METADATA_KEY] not in samples:
            sample_status = {
                "type": "SAMPLE",
                "igocomplete": f.metadata["igocomplete"],
                "sample": f.metadata[settings.SAMPLE_ID_METADATA_KEY],
                "status": "COMPLETED",
                "message": "File %s request metadata updated",
                "code": None,
            }
            samples.append(f.metadata[settings.SAMPLE_ID_METADATA_KEY])
            sample_status_list.append(sample_status)
        ddiff = DeepDiff(f.metadata, new_metadata, ignore_order=True)
        diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, f.version + 1)
        message = "Updating file metadata: %s, details in file %s\n" % (f.file.path, diff_file_name)
        update = RedeliveryUpdateEvent(job_group_notifier_id, message).to_dict()
        diff_details_event = LocalStoreFileEvent(job_group_notifier_id, diff_file_name, str(ddiff)).to_dict()
        send_notification.delay(update)
        send_notification.delay(diff_details_event)
        update_file_object(f.file, f.file.path, new_metadata)

    _generate_ticket_description(
        request_id, str(job_group.id), job_group_notifier_id, sample_status_list, [], request_metadata
    )

    request_callback(request_id, recipe, sample_status_list, job_group, job_group_notifier)


@shared_task
def update_sample_job(input_data):
    data = json.loads(input_data)
    primary_id = data.get(settings.SAMPLE_ID_METADATA_KEY)
    files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: primary_id}).all()
    file_paths = [f.file.path for f in files]
    recipe = data.get(settings.RECIPE_METADATA_KEY)
    additional_properties = data.pop("additionalProperties")
    request_id = additional_properties["igoRequestId"]

    if not files:
        logger.warning("Nothing to update %s. Creating new files." % primary_id)
        project_id = data.get(settings.PROJECT_ID_METADATA_KEY)
        project_manager_name = data.get("projectManagerName")
        pi_email = data.get("piEmail")
        lab_head_name = data.get("labHeadName")
        lab_head_email = data.get("labHeadEmail")
        investigator_name = data.get("investigatorName")
        investigator_email = data.get("investigatorEmail")
        data_analyst_name = data.get("dataAnalystName")
        data_analyst_email = data.get("dataAnalystEmail")
        other_contact_emails = data.get("otherContactEmails")
        data_access_email = data.get("dataAccessEmails")
        qc_access_email = data.get("qcAccessEmails")
    else:
        project_id = files[0].metadata.get(settings.PROJECT_ID_METADATA_KEY)
        project_manager_name = files[0].metadata.get("projectManagerName")
        pi_email = files[0].metadata.get("piEmail")
        lab_head_name = files[0].metadata.get("labHeadName")
        lab_head_email = files[0].metadata.get("labHeadEmail")
        investigator_name = files[0].metadata.get("investigatorName")
        investigator_email = files[0].metadata.get("investigatorEmail")
        data_analyst_name = files[0].metadata.get("dataAnalystName")
        data_analyst_email = files[0].metadata.get("dataAnalystEmail")
        other_contact_emails = files[0].metadata.get("otherContactEmails")
        data_access_email = files[0].metadata.get("dataAccessEmails")
        qc_access_email = files[0].metadata.get("qcAccessEmails")

    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: request_id,
        settings.PROJECT_ID_METADATA_KEY: project_id,
        settings.RECIPE_METADATA_KEY: recipe,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        "labHeadName": lab_head_name,
        "labHeadEmail": lab_head_email,
        "investigatorName": investigator_name,
        "investigatorEmail": investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }

    job_group = JobGroup()
    job_group.save()
    job_group_notifier_id = notifier_start(job_group, request_id)
    job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)

    redelivery_event = RedeliveryEvent(job_group_notifier_id).to_dict()
    send_notification.delay(redelivery_event)

    igocomplete = True
    primary_id = data["primaryId"]
    logger.info("Parsing sample: %s" % primary_id)
    libraries = data.pop("libraries")
    for library in libraries:
        logger.info("Processing library %s" % library)
        runs = library.pop("runs")
        for run in runs:
            logger.info("Processing run %s" % run)
            fastqs = run.pop("fastqs")
            for fastq in fastqs:
                logger.info("Adding file %s" % fastq)
                try:
                    f = FileRepository.filter(path=fastq).first()
                    if f:
                        new_metadata = f.metadata
                        new_metadata.update(request_metadata)
                    create_or_update_file(
                        fastq,
                        request_id,
                        settings.IMPORT_FILE_GROUP,
                        "fastq",
                        igocomplete,
                        data,
                        library,
                        run,
                        request_metadata,
                        R1_or_R2(fastq),
                    )
                    ddiff = DeepDiff(f.metadata, new_metadata, ignore_order=True)
                    diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, f.version + 1)
                    message = "Updating file metadata: %s, details in file %s\n" % (f.file.path, diff_file_name)
                    update = RedeliveryUpdateEvent(job_group_notifier_id, message).to_dict()
                    diff_details_event = LocalStoreFileEvent(
                        job_group_notifier_id, diff_file_name, str(ddiff)
                    ).to_dict()
                    send_notification.delay(update)
                    send_notification.delay(diff_details_event)
                except Exception as e:
                    logger.error(e)

    sample_status = {
        "type": "SAMPLE",
        "igocomplete": True,
        "sample": primary_id,
        "status": "COMPLETED",
        "message": "File %s request metadata updated",
        "code": None,
    }
    request_callback(request_id, recipe, [sample_status], job_group, job_group_notifier)


def get_run_id_from_string(string):
    """
    Parse the runID from a character string
    Split on the final '_' in the string

    Examples
    --------
        get_run_id_from_string("JAX_0397_BHCYYWBBXY")
        >>> JAX_0397
    """
    parts = string.split("_")
    if len(parts) > 1:
        parts.pop(-1)
        output = "_".join(parts)
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
    file_type_obj = FileType.objects.filter(name="fastq").first()
    assays = ETLConfiguration.objects.first()
    assay_list = assays.all_recipes
    run_id = None
    preservation_type = None
    recipe = None
    try:
        parts = filepath.split("/")
        path_shift = 0
        # path_shift needed for /ifs/archive/GCL/hiseq/ -> /igo/delivery/ transition
        if "igo" in parts[1]:
            path_shift = 2
        run_id = get_run_id_from_string(parts[6 - path_shift])
        pooled_normal_folder = parts[8 - path_shift]
        preservation_type = pooled_normal_folder
        preservation_type = preservation_type.split("Sample_")[1]
        preservation_type = preservation_type.split("POOLEDNORMAL")[0]
        potential_recipe = list(filter(lambda single_assay: single_assay in pooled_normal_folder, assay_list))
        if potential_recipe:
            potential_recipe.sort(key=len, reverse=True)
            recipe = potential_recipe[0]
    except Exception as e:
        raise FailedToFetchPoolNormalException("Failed to parse metadata for pooled normal file %s" % filepath)
    if preservation_type not in ("FFPE", "FROZEN", "MOUSE"):
        logger.info("Invalid preservation type %s" % preservation_type)
        return
    if recipe in assays.disabled_recipes:
        logger.info("Recipe %s, is marked as disabled" % recipe)
        return
    if None in [run_id, preservation_type, recipe]:
        logger.info("Invalid metadata runId:%s preservation:%s recipe:%s" % (run_id, preservation_type, recipe))
        return
    metadata = {"runId": run_id, "preservation": preservation_type, settings.RECIPE_METADATA_KEY: recipe}
    try:
        new_path = CopyService.remap(recipe, filepath)
        if new_path != filepath:
            CopyService.copy(filepath, new_path)
    except Exception as e:
        logger.error("Failed to copy file %s." % (filepath,))
        raise FailedToFetchPoolNormalException("Failed to copy file %s. Error %s" % (filepath, str(e)))

    try:
        f = File.objects.create(
            file_name=os.path.basename(filepath), path=filepath, file_group=file_group_obj, file_type=file_type_obj
        )
        f.save()
        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
    except Exception as e:
        logger.info("File already exist %s." % filepath)


def validate_sample(sample_id, libraries, igocomplete, redelivery=False):
    conflict = False
    missing_fastq = False
    invalid_number_of_fastq = False
    failed_runs = []
    conflict_files = []
    if not libraries:
        if igocomplete:
            raise ErrorInconsistentDataException(
                "Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id
            )
        else:
            raise MissingDataException("Failed to fetch SampleManifest for sampleId:%s. Libraries empty" % sample_id)
    for library in libraries:
        runs = library.get("runs")
        if not runs:
            logger.error("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
            if igocomplete:
                raise ErrorInconsistentDataException(
                    "Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id
                )
            else:
                raise MissingDataException("Failed to fetch SampleManifest for sampleId:%s. Runs empty" % sample_id)
        run_dict = convert_to_dict(runs)
        for run in run_dict.values():
            fastqs = run.get("fastqs")
            if not fastqs:
                logger.error("Failed to fetch SampleManifest for sampleId:%s. Fastqs empty" % sample_id)
                missing_fastq = True
                run_id = run["runId"] if run["runId"] else "None"
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
                "Missing fastq files for igcomplete: %s sample %s : %s"
                % (igocomplete, sample_id, " ".join(failed_runs))
            )
        else:
            raise MissingDataException(
                "Missing fastq files for igcomplete: %s sample %s : %s"
                % (igocomplete, sample_id, " ".join(failed_runs))
            )
    if not redelivery:
        if conflict:
            res_str = ""
            for f in conflict_files:
                res_str += "%s: %s" % (f[0], f[1])
            raise ErrorInconsistentDataException("Conflict of fastq file(s) %s" % res_str)


def R1_or_R2(filename):
    reversed_filename = "".join(reversed(filename))
    R1_idx = reversed_filename.find("1R")
    R2_idx = reversed_filename.find("2R")
    if R1_idx == -1 and R2_idx == -1:
        return "UNKNOWN"
    elif R1_idx > 0 and R2_idx == -1:
        return "R1"
    elif R2_idx > 0 and R1_idx == -1:
        return "R2"
    elif R1_idx > 0 and R2_idx > 0:
        if R1_idx < R2_idx:
            return "R1"
        else:
            return "R2"
    return "UNKNOWN"


def convert_to_dict(runs):
    run_dict = dict()
    for run in runs:
        if not run_dict.get(run["runId"]):
            run_dict[run["runId"]] = run
        else:
            if run_dict[run["runId"]].get("fastqs"):
                logger.error("Fastq empty")
                if run_dict[run["runId"]]["fastqs"][0] != run["fastqs"][0]:
                    logger.error(
                        "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][0], run["fastqs"][0])
                    )
                    raise FailedToFetchSampleException(
                        "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][0], run["fastqs"][0])
                    )
                if run_dict[run["runId"]]["fastqs"][1] != run["fastqs"][1]:
                    logger.error(
                        "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][1], run["fastqs"][1])
                    )
                    raise FailedToFetchSampleException(
                        "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][1], run["fastqs"][1])
                    )
    return run_dict


def create_or_update_file(
    path, request_id, file_group_id, file_type, igocomplete, data, library, run, request_metadata, r
):
    try:
        file_group_obj = FileGroup.objects.get(id=file_group_id)
        file_type_obj = FileType.objects.filter(name=file_type).first()
        lims_metadata = copy.deepcopy(data)
        library_copy = copy.deepcopy(library)
        lims_metadata[settings.REQUEST_ID_METADATA_KEY] = request_id
        lims_metadata["igocomplete"] = igocomplete
        lims_metadata["R"] = r
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
        logger.info(metadata)
        # validator.validate(metadata)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        recipe = metadata.get(settings.RECIPE_METADATA_KEY, "")
        new_path = CopyService.remap(recipe, path)  # Get copied file path
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
            create_file_object(new_path, file_group_obj, metadata, file_type_obj)
        else:
            update_file_object(f.file, f.file.path, metadata)


def format_metadata(original_metadata):
    metadata = copy.deepcopy(original_metadata)
    sample_name = original_metadata.get("cmoSampleName", None)
    sample_class = original_metadata.get(settings.SAMPLE_CLASS_METADATA_KEY, None)
    # ciTag is the new field which needs to be used for the operators
    metadata["ciTag"] = format_sample_name(sample_name, sample_class)
    metadata["sequencingCenter"] = "MSKCC"
    metadata["platform"] = "Illumina"
    return metadata


def create_file_object(path, file_group, metadata, file_type):
    try:
        f = File.objects.create(file_name=os.path.basename(path), path=path, file_group=file_group, file_type=file_type)
        f.save()

        fm = FileMetadata(file=f, metadata=metadata)
        fm.save()
        Job.objects.create(
            run=TYPES["CALCULATE_CHECKSUM"],
            args={"file_id": str(f.id), "path": path},
            status=JobStatus.CREATED,
            max_retry=3,
            children=[],
        )
        import_metadata = ImportMetadata.objects.create(file=f, metadata=metadata)
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
        data["user"] = user.id
    except User.DoesNotExist:
        user = None
    serializer = UpdateFileSerializer(file_object, data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        logger.error("Failed to update file %s: Error %s" % (path, serializer.errors))
        raise FailedToFetchSampleException(
            "Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors)
        )


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


def _generate_ticket_description(
    request_id, job_group_id, job_group_notifier_id, sample_list, pooled_normal_list, request_metadata
):
    all_jobs = []

    cnt_samples_completed = 0
    cnt_samples_failed = 0

    all_jobs.extend(sample_list)
    all_jobs.extend(pooled_normal_list)

    number_of_tumors = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id, "tumorOrNormal": "Tumor"},
        values_metadata=settings.SAMPLE_ID_METADATA_KEY,
    ).count()
    number_of_normals = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id, "tumorOrNormal": "Normal"},
        values_metadata=settings.SAMPLE_ID_METADATA_KEY,
    ).count()

    recipe = request_metadata.get(settings.RECIPE_METADATA_KEY)
    data_analyst_email = request_metadata.get("dataAnalystEmail", "")
    data_analyst_name = request_metadata.get("dataAnalystName", "")
    investigator_email = request_metadata.get("investigatorEmail", "")
    investigator_name = request_metadata.get("investigatorName", "")
    lab_head_email = request_metadata.get("labHeadEmail", "")
    lab_head_name = request_metadata.get("labHeadName", "")
    pi_email = request_metadata.get("piEmail", "")
    project_manager_name = request_metadata.get("projectManagerName", "")
    qc_access_emails = request_metadata.get("qcAccessEmails", "")
    data_access_emails = request_metadata.get("dataAccessEmails", "")
    other_contact_emails = request_metadata.get("otherContactEmails", "")

    event = ETLImportEvent(
        str(job_group_notifier_id),
        str(job_group_id),
        request_id,
        cnt_samples_completed,
        cnt_samples_failed,
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
        len(pooled_normal_list),
        data_access_emails,
        other_contact_emails,
    )
    e = event.to_dict()
    send_notification.delay(e)

    etl_event = ETLJobsLinksEvent(job_group_notifier_id, request_id, all_jobs)
    etl_e = etl_event.to_dict()
    send_notification.delay(etl_e)