import os
import copy
import json
import logging
import re

from deepdiff import DeepDiff
from datetime import datetime, timedelta
from dateutil.parser import parse
from celery import shared_task
from django.conf import settings
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
    LocalStoreFileEvent,
    ExternalEmailEvent,
    OnlyNormalSamplesEvent,
    WESJobFailedEvent,
    VoyagerCantProcessRequestAllNormalsEvent,
    SMILEUpdateEvent,
)
from notifier.tasks import send_notification, notifier_start
from notifier.helper import get_emails_to_notify
from beagle_etl.exceptions import ETLExceptions
from beagle_etl.models import (
    Operator,
    ETLConfiguration,
    SMILEMessage,
    SmileMessageStatus,
    RequestCallbackJob,
    RequestCallbackJobStatus,
    initialize_normalizer,
    CopyFileTask
)
from file_system.serializers import UpdateFileSerializer
from file_system.exceptions import MetadataValidationException
from file_system.repository.file_repository import FileRepository
from file_system.models import File, FileGroup, FileMetadata, FileType, Request, Sample
from beagle_etl.exceptions import (
    FailedToFetchSampleException,
    FailedToSubmitToOperatorException,
    ErrorInconsistentDataException,
    MissingDataException,
    FailedToFetchPoolNormalException,
    FailedToCalculateChecksum,
    FailedToCopyFilePermissionDeniedException,
    FailedToCopyFileException,
    IncorrectlyFormattedPrimaryId,
    FailedToLocateTheFileException,
)

from runner.tasks import create_jobs_from_request
from file_system.serializers import CreateFileSerializer
from file_system.helper.checksum import sha1, FailedToCalculateChecksum
from runner.operator.helper import format_sample_name
from beagle_etl.copy_service import CopyService
from beagle_etl.jobs.helper_jobs import check_file_permissions, fix_path_iris
from beagle_etl.jobs.notification_helper import _generate_ticket_description
from django.contrib.auth.models import User
from study.models import Study
from study.objects import StudyObject
from django.db.models import Q


logger = logging.getLogger(__name__)


def fetch_operators_wfastq(fastq_metadata):
    # Limit Potential Operators with OR query
    query = Q()
    for key, value in fastq_metadata.items():
        query |= Q(recipes_json__contains=[{key: value}])
        query |= Q(recipes_json__contains=[{key: [value]}])  # could be a list
    candidates = Operator.objects.filter(query)

    # Make sure operator all json_recipes key/values exist in fastq metadata
    operators = []
    for obj in candidates:
        for recipe_dict in obj.recipes_json:
            if all(
                fastq_metadata.get(key, "") in normalize_fastq_value(recipe_dict.get(key, [])) for key in recipe_dict
            ):
                operators.append(obj)
    return operators


def create_request_callback_instance(
    request_id, smile_message, recipe, sample_jobs, job_group, job_group_notifier, delay=0, **kwargs
):
    fastq_metadata = kwargs.get("fastq_metadata", None)
    request = RequestCallbackJob.objects.filter(request_id=request_id, status=RequestCallbackJobStatus.PENDING).first()
    if not request:
        RequestCallbackJob.objects.create(
            request_id=request_id,
            smile_message=smile_message,
            recipe=recipe,
            fastq_metadata=fastq_metadata,
            samples=sample_jobs,
            job_group=job_group,
            job_group_notifier=job_group_notifier,
            delay=delay,
        )
    else:
        request.samples.extend(sample_jobs)
        request.save()


def request_update_notification(request_id):
    last = SMILEMessage.objects.filter(request_id__startswith=request_id).order_by("-created_date").first()
    if last.topic in (settings.METADB_NATS_REQUEST_UPDATE, settings.METADB_NATS_SAMPLE_UPDATE):
        logger.info(f"Sending notifications about {request_id} update")
        send_to = get_emails_to_notify(request_id, "SMILEUpdateEvent")
        for email in send_to:
            event = SMILEUpdateEvent(
                job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP,
                email_to=email,
                email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                subject=f"SMILE sent update for request {request_id}",
                request_id=request_id,
            ).to_dict()
            send_notification.delay(event)
    else:
        logger.info(f"SMILE sent new project {request_id}")


@shared_task
def new_request(message_id):
    message = SMILEMessage.objects.get(id=message_id)
    log = ""
    data = json.loads(message.message)
    request_id = data.get(settings.REQUEST_ID_METADATA_KEY)

    if not data.get(settings.IS_CMO_REQUEST):
        logger.info(f"Request {request_id} is not CMO Request")
        log += f"Request {request_id} is not CMO Request\n"
        message.status = SmileMessageStatus.COMPLETED
        message.log = log
        message.save()
        return

    gene_panel = data.get(settings.RECIPE_METADATA_KEY)
    message.gene_panel = gene_panel
    message.save(update_fields=["gene_panel"])
    log += f"Importing new request: {request_id} with genePanel: {gene_panel}\n"
    logger.info(f"Importing new request: {request_id} with genePanel: {gene_panel}\n")

    sample_jobs = []
    valid_samples = set()

    samples = data.get("samples")
    for idx, sample in enumerate(samples):
        igocomplete = sample.get("igoComplete")
        try:
            validate_sample(sample["primaryId"], sample.get("libraries", []), igocomplete, gene_panel)
            sample_status = {
                "type": "SAMPLE",
                "igocomplete": igocomplete,
                "sample": sample["primaryId"],
                "status": "COMPLETED",
                "message": "",
                "code": None,
            }
            sample_jobs.append(sample_status)
            valid_samples.add(sample["primaryId"])
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
    message.sample_status = sample_jobs
    message.save(update_fields=("sample_status",))

    job_group = JobGroup.objects.create()
    message.job_group = job_group
    job_group_notifier_id = notifier_start(job_group, request_id)
    job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id) if job_group_notifier_id else None
    message.job_group_notifier = job_group_notifier
    message.save(
        update_fields=(
            "job_group",
            "job_group_notifier",
        )
    )

    project_id = data.get(settings.PROJECT_ID_METADATA_KEY)
    recipe = data.get(settings.RECIPE_METADATA_KEY)
    set_recipe_event = ETLSetRecipeEvent(str(job_group_notifier_id), recipe).to_dict()
    send_notification.delay(set_recipe_event)

    project_manager_name = data.get("projectManagerName")
    pi_email = data.get("piEmail")
    lab_head_name = data.get(settings.LAB_HEAD_NAME_METADATA_KEY)
    lab_head_email = data.get(settings.LAB_HEAD_EMAIL_METADATA_KEY)
    investigator_name = data.get(settings.INVESTIGATOR_NAME_METADATA_KEY)
    investigator_email = data.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY)
    data_analyst_name = data.get("dataAnalystName")
    data_analyst_email = data.get("dataAnalystEmail")
    other_contact_emails = data.get("otherContactEmails")
    data_access_email = data.get("dataAccessEmails")
    qc_access_email = data.get("qcAccessEmails")

    study, _ = Study.objects.get_or_create(study_id=StudyObject.generate_study_id(lab_head_email))

    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: request_id,
        settings.PROJECT_ID_METADATA_KEY: project_id,
        settings.RECIPE_METADATA_KEY: recipe,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        settings.LAB_HEAD_NAME_METADATA_KEY: lab_head_name,
        settings.LAB_HEAD_EMAIL_METADATA_KEY: lab_head_email,
        settings.INVESTIGATOR_NAME_METADATA_KEY: investigator_name,
        settings.INVESTIGATOR_EMAIL_METADATA_KEY: investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }
    if data.get("deliveryDate"):
        delivery_date = datetime.fromtimestamp(data["deliveryDate"] / 1000)
    else:
        delivery_date = datetime.now()
    data["deliveryDate"] = delivery_date

    smile_job_status = message.status

    for idx, sample in enumerate(data.get("samples")):
        sample_id = sample["primaryId"]
        if sample_id not in valid_samples:
            smile_job_status = SmileMessageStatus.FAILED
            continue
        igocomplete = sample.get("igoComplete")
        logger.info("Parsing sample: %s" % sample_id)
        libraries = sample.pop("libraries")
        for library in libraries:
            logger.info("Processing library %s" % library)
            runs = library.pop("runs")
            for run in runs:
                logger.info("Processing run %s" % run)
                fastqs = run.pop("fastqs")
                for fastq in fastqs:
                    fastq_location = fix_path_iris(fastq)
                    logger.info("Adding file %s" % fastq_location)
                    try:
                        create_or_update_file(
                            message,
                            fastq_location,
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
        sample = Sample.objects.filter(sample_id=sample_id, latest=True).first()
        if sample:
            study.samples.add(sample)

    request = Request.objects.filter(request_id=request_id, latest=True).first()
    if not request:
        log += f"No samples imported for request {request_id}"
        logger.error(f"No samples imported for request {request_id}")
        smile_job_status = SmileMessageStatus.FAILED
    else:
        study.requests.add(request)
    pooled_normal = data.get("pooledNormals") if data.get("pooledNormals") is not None else []
    pooled_normal_jobs = []
    for pn in pooled_normal:
        try:
            create_pooled_normal(message, pn, str(settings.POOLED_NORMAL_FILE_GROUP))
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

    if CopyFileTask.objects.filter(smile_message=message).count() == 0 and smile_job_status != SmileMessageStatus.FAILED:
        smile_job_status = SmileMessageStatus.COMPLETED

    message.status = smile_job_status
    message.log = log
    message.save()


# Run Operator
def run_operator(message_id):
    msg = SMILEMessage.objects.get(message_id=message_id)
    fastq_metadata = fetch_fastq_metadata(msg.request_id)
    create_request_callback_instance(
        msg.request_id,
        msg,
        msg.gene_panel,
        msg.sample_status,
        msg.job_group,
        msg.job_group_notifier,
        fastq_metadata=fastq_metadata,
    )


def normalize_fastq_value(val):
    if isinstance(val, list):
        return set(val)
    elif isinstance(val, str):
        return {val}
    else:
        return set()


@shared_task
def request_callback(request_id, recipe, fastq_metadata, sample_jobs, job_group_id=None, job_group_notifier_id=None):
    """
    :param request_id: 08944_B
    :param recipe: IMPACT438
    :param sample_jobs: sample_jobs[]
    :param job_group: JobGroup instance
    :param job_group_notifier: JobGroupNotifier instance
    :return:
    """
    assays = ETLConfiguration.objects.first()

    try:
        job_group = JobGroup.objects.get(id=job_group_id)
    except JobGroup.DoesNotExist:
        job_group = None

    try:
        job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)
    except JobGroupNotifier.DoesNotExist:
        job_group_notifier = None

    request_update_notification(request_id)

    if recipe in settings.WES_ASSAYS:
        for job in sample_jobs:
            if job["igocomplete"] and job["status"] != "COMPLETED":
                wes_job_failed = WESJobFailedEvent(job_group_notifier_id, recipe)
                send_notification.delay(wes_job_failed.to_dict())
    if not recipe:
        raise FailedToSubmitToOperatorException(
            "Not enough metadata to choose the operator for requestId:%s" % request_id
        )

    if not all(item in assays.all_recipes for item in (recipe,)):
        ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(ci_review_e)
        set_unknown_assay_label = SetLabelEvent(job_group_notifier_id, "unrecognized_assay").to_dict()
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

    if any(
        item in assays.disabled_recipes
        for item in [
            recipe,
        ]
    ):
        not_for_ci = NotForCIReviewEvent(job_group_notifier_id).to_dict()
        send_notification.delay(not_for_ci)
        disabled_assay_event = DisabledAssayEvent(job_group_notifier_id, recipe).to_dict()
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
        no_samples_event = AdminHoldEvent(job_group_notifier_id).to_dict()
        send_notification.delay(no_samples_event)
        return []

    run_dates = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
        file_group=settings.IMPORT_FILE_GROUP,
        values_metadata=settings.RUN_DATE_METADATA_KEY,
    ).all()

    if not run_dates:
        logger.info(f"Request doesn't have run_date specified. Skip running.")
        return []

    run_dates = sorted([parse(d) for d in run_dates])

    if datetime.now().date() - run_dates[-1].date() > timedelta(days=settings.OLD_REQUEST_TIMEDELTA):
        logger.info(f"Request older than {settings.OLD_REQUEST_TIMEDELTA} days imported. Skip running.")
        return []

    for job in sample_jobs:
        if job["igocomplete"] and job["status"] != "COMPLETED":
            ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
            send_notification.delay(ci_review_e)

    lab_head_email = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.LAB_HEAD_EMAIL_METADATA_KEY
    ).first()
    try:
        if lab_head_email.split("@")[1] != "mskcc.org":
            event = ExternalEmailEvent(job_group_notifier_id, request_id).to_dict()
            send_notification.delay(event)
    except Exception:
        logger.error("Failed to check labHeadEmail")

    if (
        len(
            FileRepository.filter(
                metadata={settings.REQUEST_ID_METADATA_KEY: request_id, settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor"}
            )
        )
        == 0
    ):
        samples = list(
            FileRepository.filter(
                metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
                values_metadata=settings.INVESTIGATOR_SAMPLE_ID_METADATA_KEY,
            )
        )
        only_normal_samples_event = OnlyNormalSamplesEvent(job_group_notifier_id, request_id).to_dict()
        send_notification.delay(only_normal_samples_event)
        send_to = get_emails_to_notify(request_id, "VoyagerCantProcessRequestAllNormalsEvent")
        for email in send_to:
            event = VoyagerCantProcessRequestAllNormalsEvent(
                job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP,
                email_to=email,
                email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                subject="Voyager Status: All Normals",
                request_id=request_id,
                samples=samples,
            ).to_dict()
            send_notification.delay(event)

        if recipe in settings.ASSAYS_ADMIN_HOLD_ONLY_NORMALS:
            admin_hold_event = AdminHoldEvent(str(job_group_notifier.id)).to_dict()
            send_notification.delay(admin_hold_event)
            return []
    # Find operators that match fastq_metadata
    operators = fetch_operators_wfastq(fastq_metadata)
    print(f"Operators matched with {request_id} during request_callback: {operators}")
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
            error_label = SetLabelEvent(job_group_notifier_id, "operator_inactive").to_dict()
            send_notification.delay(error_label)
            ci_review_e = SetCIReviewEvent(job_group_notifier_id).to_dict()
            send_notification.delay(ci_review_e)
        else:
            logger.info("Submitting request_id %s to %s operator" % (request_id, operator.class_name))
            # Rewrite this to use SMILEMessage
            # if Job.objects.filter(
            #     job_group=job_group, args__request_id=request_id, run=TYPES["SAMPLE"], status=JobStatus.FAILED
            # ).all():
            #     partialy_complete_event = ETLImportPartiallyCompleteEvent(job_notifier=job_group_notifier_id).to_dict()
            #     send_notification.delay(partialy_complete_event)
            # else:
            #     complete_event = ETLImportCompleteEvent(job_notifier=job_group_notifier_id).to_dict()
            #     send_notification.delay(complete_event)
            notify = SMILEMessage.objects.filter(request_id__startswith=request_id).count() == 1
            create_jobs_from_request.delay(request_id, operator.id, str(job_group.id), notify=notify)
    return []


@shared_task
def update_request_job(message_id, job_group, job_group_notifier):
    job_group_notifier_id = str(job_group_notifier.id)
    message = SMILEMessage.objects.get(id=message_id)
    metadata = json.loads(message.message)[-1]
    data = json.loads(metadata["requestMetadataJson"])
    request_id = metadata.get(settings.REQUEST_ID_METADATA_KEY)
    files = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_group=settings.IMPORT_FILE_GROUP
    )

    project_id = data.get("projectId")
    recipe = data.get(settings.LIMS_RECIPE_METADATA_KEY)
    redelivery_event = RedeliveryEvent(job_group_notifier_id).to_dict()
    send_notification.delay(redelivery_event)

    project_manager_name = data.get("projectManagerName")
    pi_email = data.get("piEmail")
    lab_head_name = data.get(settings.LAB_HEAD_NAME_METADATA_KEY)
    lab_head_email = data.get(settings.LAB_HEAD_EMAIL_METADATA_KEY)
    investigator_name = data.get(settings.INVESTIGATOR_NAME_METADATA_KEY)
    investigator_email = data.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY)
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
        settings.LAB_HEAD_NAME_METADATA_KEY: lab_head_name,
        settings.LAB_HEAD_EMAIL_METADATA_KEY: lab_head_email,
        settings.INVESTIGATOR_NAME_METADATA_KEY: investigator_name,
        settings.INVESTIGATOR_EMAIL_METADATA_KEY: investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
    }

    samples = list()
    sample_status_list = list()
    for f in files:
        new_metadata = copy.deepcopy(f.metadata)
        new_metadata.update(request_metadata)
        if f.metadata[settings.SAMPLE_ID_METADATA_KEY] not in samples:
            sample_status = {
                "type": "SAMPLE",
                "igocomplete": f.metadata[settings.IGO_COMPLETE_METADATA_KEY],
                "sample": f.metadata[settings.SAMPLE_ID_METADATA_KEY],
                "status": "COMPLETED",
                "message": f"File {f.file.path} request metadata updated",
                "code": None,
            }
            samples.append(f.metadata[settings.SAMPLE_ID_METADATA_KEY])
            sample_status_list.append(sample_status)
        ddiff = DeepDiff(f.metadata, new_metadata, ignore_order=True)
        diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, f.version + 1)
        msg = "Updating file metadata: %s, details in file %s\n" % (f.file.path, diff_file_name)
        update = RedeliveryUpdateEvent(job_group_notifier_id, msg).to_dict()
        diff_details_event = LocalStoreFileEvent(job_group_notifier_id, diff_file_name, str(ddiff)).to_dict()
        send_notification.delay(update)
        send_notification.delay(diff_details_event)
        update_file_object(f.file, f.file.path, new_metadata)

    pooled_normal = data.get("pooledNormals", [])
    if pooled_normal is None:
        pooled_normal = []
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
    message.status = SmileMessageStatus.COMPLETED
    message.save()

    return request_metadata, pooled_normal


def fetch_request_metadata(request_id):
    file_example = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_group=settings.IMPORT_FILE_GROUP
    ).first()
    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: file_example.metadata[settings.REQUEST_ID_METADATA_KEY],
        settings.PROJECT_ID_METADATA_KEY: file_example.metadata[settings.PROJECT_ID_METADATA_KEY],
        settings.RECIPE_METADATA_KEY: file_example.metadata[settings.RECIPE_METADATA_KEY],
        "projectManagerName": file_example.metadata["projectManagerName"],
        "piEmail": file_example.metadata["piEmail"],
        settings.LAB_HEAD_NAME_METADATA_KEY: file_example.metadata[settings.LAB_HEAD_NAME_METADATA_KEY],
        settings.LAB_HEAD_EMAIL_METADATA_KEY: file_example.metadata[settings.LAB_HEAD_EMAIL_METADATA_KEY],
        settings.INVESTIGATOR_NAME_METADATA_KEY: file_example.metadata[settings.INVESTIGATOR_NAME_METADATA_KEY],
        settings.INVESTIGATOR_EMAIL_METADATA_KEY: file_example.metadata[settings.INVESTIGATOR_EMAIL_METADATA_KEY],
        "dataAnalystName": file_example.metadata["dataAnalystName"],
        "dataAnalystEmail": file_example.metadata["dataAnalystEmail"],
        "otherContactEmails": file_example.metadata["otherContactEmails"],
        "dataAccessEmails": file_example.metadata["dataAccessEmails"],
        "qcAccessEmails": file_example.metadata["qcAccessEmails"],
    }
    return request_metadata


def fetch_fastq_metadata(request_id):
    """
    input: request_id <string>: request_id received in a smile message.
    output:
        - fastq_metadata <dict>: fastq metadata that is generalized to an entire request.
    """
    fastq_file = (
        FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_group=settings.IMPORT_FILE_GROUP
        )
        .values_list("metadata", flat=True)
        .first()
    )
    if fastq_file:
        fastq_metadata = {
            settings.BAITSET_METADATA_KEY: fastq_file.get(settings.BAITSET_METADATA_KEY),
            "runMode": fastq_file.get("runMode"),
            "species": fastq_file.get("species"),
            "platform": fastq_file.get("platform"),
            "genePanel": fastq_file.get("genePanel"),
            settings.REQUEST_ID_METADATA_KEY: fastq_file.get(settings.REQUEST_ID_METADATA_KEY),
            settings.PROJECT_ID_METADATA_KEY: fastq_file.get(settings.PROJECT_ID_METADATA_KEY),
            settings.ONCOTREE_METADATA_KEY: fastq_file.get(settings.ONCOTREE_METADATA_KEY),
            settings.PRESERVATION_METADATA_KEY: fastq_file.get(settings.PRESERVATION_METADATA_KEY),
            "sampleOrigin": fastq_file.get("sampleOrigin"),
        }
    else:
        fastq_metadata = {}
    return fastq_metadata


@shared_task
def update_job(request_id):
    sample_update_messages = (
        SMILEMessage.objects.filter(
            request_id__startswith=request_id,
            topic=settings.METADB_NATS_SAMPLE_UPDATE,
            status=SmileMessageStatus.PENDING,
        )
        .order_by("created_date")
        .all()
    )
    request_update_messages = (
        SMILEMessage.objects.filter(
            request_id__startswith=request_id,
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            status=SmileMessageStatus.PENDING,
        )
        .order_by("created_date")
        .all()
    )

    job_group = JobGroup()
    job_group.save()
    job_group_notifier_id = notifier_start(job_group, request_id)
    job_group_notifier = JobGroupNotifier.objects.get(id=job_group_notifier_id)
    sample_status = []
    for msg in sample_update_messages:
        sample_status.extend(update_sample_job(str(msg.id), job_group, job_group_notifier))
    request_metadata = dict()
    pooled_normal = list()
    for msg in request_update_messages:
        request_metadata, pooled_normal = update_request_job(str(msg.id), job_group, job_group_notifier)

    if not request_metadata:
        request_metadata = fetch_request_metadata(request_id)
    fastq_metadata = fetch_fastq_metadata(request_id)
    recipe = fastq_metadata.get(settings.RECIPE_METADATA_KEY)
    _generate_ticket_description(
        request_id, str(job_group.id), job_group_notifier_id, sample_status, pooled_normal, request_metadata
    )


@shared_task
def update_sample_job(message_id, job_group, job_group_notifier):
    message = SMILEMessage.objects.get(id=message_id)
    job_group_notifier_id = str(job_group_notifier.id)
    data = json.loads(message.message)
    latest = data["latestSampleMetadata"]
    latest["datasource"] = data["datasource"]
    latest["sampleAliases"] = data["sampleAliases"]
    latest["smileSampleId"] = data["smileSampleId"]
    latest["smilePatientId"] = data["patient"]["smilePatientId"]
    latest["patientAliases"] = data["patient"]["patientAliases"]
    primary_id = latest.get(settings.SAMPLE_ID_METADATA_KEY)
    files = FileRepository.filter(
        metadata={settings.SAMPLE_ID_METADATA_KEY: primary_id}, file_group=settings.IMPORT_FILE_GROUP
    ).all()
    file_paths = [f.file.path for f in files]
    new_files = []
    recipe = latest.get(settings.RECIPE_METADATA_KEY)
    request_id = latest.get(settings.REQUEST_ID_METADATA_KEY)
    igocomplete = latest.get(settings.IGO_COMPLETE_METADATA_KEY)

    if not files:
        logger.warning("Nothing to update %s. Creating new files." % primary_id)
        project_id = latest.get(settings.PROJECT_ID_METADATA_KEY)
        project_manager_name = latest.get("projectManagerName")
        pi_email = latest.get("piEmail")
        lab_head_name = latest.get(settings.LAB_HEAD_NAME_METADATA_KEY)
        lab_head_email = latest.get(settings.LAB_HEAD_EMAIL_METADATA_KEY)
        investigator_name = latest.get(settings.INVESTIGATOR_NAME_METADATA_KEY)
        investigator_email = latest.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY)
        data_analyst_name = latest.get("dataAnalystName")
        data_analyst_email = latest.get("dataAnalystEmail")
        other_contact_emails = latest.get("otherContactEmails")
        data_access_email = latest.get("dataAccessEmails")
        qc_access_email = latest.get("qcAccessEmails")
        oncotree_code = latest.get(settings.ONCOTREE_METADATA_KEY)
        datasource = latest.get("datasource")
        sample_aliases = latest.get("sampleAliases")
        smile_sample_id = latest.get("smileSampleId")
        cfdna_2dbarcode = latest.get("cfDNA2dBarcode")
        cmo_info_igo_id = latest.get("cmoInfoIgoId")
        patient_aliases = latest.get("patientAliases")
        smile_patient_id = latest.get("smilePatientId")
    else:
        project_id = files[0].metadata.get(settings.PROJECT_ID_METADATA_KEY)
        oncotree_code = files[0].metadata.get(settings.ONCOTREE_METADATA_KEY)
        project_manager_name = files[0].metadata.get("projectManagerName")
        pi_email = files[0].metadata.get("piEmail")
        lab_head_name = files[0].metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY)
        lab_head_email = files[0].metadata.get(settings.LAB_HEAD_EMAIL_METADATA_KEY)
        investigator_name = files[0].metadata.get(settings.INVESTIGATOR_NAME_METADATA_KEY)
        investigator_email = files[0].metadata.get(settings.INVESTIGATOR_EMAIL_METADATA_KEY)
        data_analyst_name = files[0].metadata.get("dataAnalystName")
        data_analyst_email = files[0].metadata.get("dataAnalystEmail")
        other_contact_emails = files[0].metadata.get("otherContactEmails")
        data_access_email = files[0].metadata.get("dataAccessEmails")
        qc_access_email = files[0].metadata.get("qcAccessEmails")
        datasource = files[0].metadata.get("datasource")
        sample_aliases = files[0].metadata.get("sampleAliases")
        smile_sample_id = files[0].metadata.get("smileSampleId")
        cfdna_2dbarcode = files[0].metadata.get("cfDNA2dBarcode")
        cmo_info_igo_id = files[0].metadata.get("cmoInfoIgoId")
        patient_aliases = files[0].metadata.get("patientAliases")
        smile_patient_id = files[0].metadata.get("smilePatientId")

    request_metadata = {
        settings.REQUEST_ID_METADATA_KEY: request_id,
        settings.PROJECT_ID_METADATA_KEY: project_id,
        settings.RECIPE_METADATA_KEY: recipe,
        settings.ONCOTREE_METADATA_KEY: oncotree_code,
        "projectManagerName": project_manager_name,
        "piEmail": pi_email,
        settings.LAB_HEAD_NAME_METADATA_KEY: lab_head_name,
        settings.LAB_HEAD_EMAIL_METADATA_KEY: lab_head_email,
        settings.INVESTIGATOR_NAME_METADATA_KEY: investigator_name,
        settings.INVESTIGATOR_EMAIL_METADATA_KEY: investigator_email,
        "dataAnalystName": data_analyst_name,
        "dataAnalystEmail": data_analyst_email,
        "otherContactEmails": other_contact_emails,
        "dataAccessEmails": data_access_email,
        "qcAccessEmails": qc_access_email,
        "datasource": datasource,
        "sampleAliases": sample_aliases,
        "smileSampleId": smile_sample_id,
        "cfDNA2dBarcode": cfdna_2dbarcode,
        "cmoInfoIgoId": cmo_info_igo_id,
        "patientAliases": patient_aliases,
        "smilePatientId": smile_patient_id,
    }

    redelivery_event = RedeliveryEvent(job_group_notifier_id).to_dict()
    send_notification.delay(redelivery_event)

    request_metadata[settings.SAMPLE_ID_METADATA_KEY] = latest[settings.SAMPLE_ID_METADATA_KEY]
    request_metadata[settings.PATIENT_ID_METADATA_KEY] = latest.get(settings.PATIENT_ID_METADATA_KEY)
    request_metadata["investigatorSampleId"] = latest.get("investigatorSampleId")
    request_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = latest.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
    request_metadata[settings.SAMPLE_NAME_METADATA_KEY] = latest.get(settings.SAMPLE_NAME_METADATA_KEY)
    request_metadata["importDate"] = latest.get("importDate")
    request_metadata["collectionYear"] = latest.get("collectionYear")
    request_metadata["tubeId"] = latest.get("tubeId")
    request_metadata["species"] = latest.get("species")
    request_metadata["sex"] = latest.get("sex")
    request_metadata["tumorOrNormal"] = latest.get("tumorOrNormal")
    request_metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = latest.get(settings.CMO_SAMPLE_CLASS_METADATA_KEY)
    request_metadata["preservation"] = latest.get("preservation")
    request_metadata[settings.SAMPLE_CLASS_METADATA_KEY] = latest.get(settings.SAMPLE_CLASS_METADATA_KEY)
    request_metadata["sampleOrigin"] = latest.get("sampleOrigin")
    request_metadata["tissueLocation"] = latest.get("tissueLocation")
    request_metadata["baitSet"] = latest.get("baitSet")
    request_metadata["qcReports"] = latest.get("qcReports")
    request_metadata["cmoSampleIdFields"] = latest.get("cmoSampleIdFields")
    request_metadata[settings.RECIPE_METADATA_KEY] = latest.get(settings.RECIPE_METADATA_KEY)
    request_metadata["igoComplete"] = igocomplete

    logger.info("Parsing sample: %s" % primary_id)
    libraries = latest.pop("libraries")
    for library in libraries:
        logger.info("Processing library %s" % library)
        runs = library.pop("runs")
        for run in runs:
            logger.info("Processing run %s" % run)
            fastqs = run.pop("fastqs")

            for fastq in fastqs:
                logger.info("Adding file %s" % fastq)
                try:
                    fastq_location = fix_path_iris(fastq)
                    new_path = CopyService.remap(recipe, fastq_location)
                    f = FileRepository.filter(path=new_path).first()
                    if f:
                        new_metadata = copy.deepcopy(f.metadata)
                        new_metadata.update(request_metadata)
                    create_or_update_file(
                        message,
                        fastq_location,
                        request_id,
                        settings.IMPORT_FILE_GROUP,
                        "fastq",
                        igocomplete,
                        latest,
                        library,
                        run,
                        request_metadata,
                        R1_or_R2(fastq),
                    )
                    new_files.append(new_path)
                    ddiff = DeepDiff(f.metadata, new_metadata, ignore_order=True)
                    diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, f.version + 1)
                    msg = "Updating file metadata: %s, details in file %s\n" % (f.file.path, diff_file_name)
                    update = RedeliveryUpdateEvent(job_group_notifier_id, msg).to_dict()
                    diff_details_event = LocalStoreFileEvent(
                        job_group_notifier_id, diff_file_name, str(ddiff)
                    ).to_dict()
                    send_notification.delay(update)
                    send_notification.delay(diff_details_event)
                except Exception as e:
                    logger.error(e)

    # Remove unnecessary files
    files_to_remove = set(file_paths) - set(new_files)
    for fi in list(files_to_remove):
        logger.info(f"Removing file {fi}.")
        File.objects.filter(path=fi, file_group_id=settings.IMPORT_FILE_GROUP).delete()

    message.status = SmileMessageStatus.COPY_FILES
    message.save()
    sample_status = {
        "type": "SAMPLE",
        "igocomplete": True,
        "sample": primary_id,
        "status": "COMPLETED",
        "message": "File %s request metadata updated",
        "code": None,
    }
    return [sample_status]


@shared_task
def not_supported(message_id):
    message = SMILEMessage.objects.get(id=message_id)
    message.status = SmileMessageStatus.NOT_SUPPORTED
    message.save()


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


def create_pooled_normal(message, filepath, file_group_id):
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
        logger.info(f"Creating pooled normal with path {filepath}")
    else:
        logger.info(f"Pooled normal with path {filepath} already exists")
        return
    file_group_obj = FileGroup.objects.get(id=file_group_id)
    file_type_obj = FileType.objects.filter(name="fastq").first()
    assays = ETLConfiguration.objects.first()
    assay_list = assays.all_recipes
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
    new_path = CopyService.remap(recipe, filepath)
    if new_path != filepath:
        CopyService.create_copy_task(message, filepath, new_path)
    try:
        f = File.objects.create(
            file_name=os.path.basename(filepath), path=filepath, file_group=file_group_obj, file_type=file_type_obj
        )
        FileMetadata.objects.create_or_update(file=f, metadata=metadata)
    except Exception as e:
        logger.info("File already exist %s." % filepath)


def validate_sample(sample_id, libraries, igocomplete, gene_panel, redelivery=False):
    conflict = False
    missing_fastq = False
    files_unavailable = False
    permission_error = False
    permission_error_files = []
    missing_files = []
    failed_runs = []
    conflict_files = []

    pattern = re.compile(settings.PRIMARY_ID_REGEX)
    if not pattern.fullmatch(sample_id):
        logger.error(f"primaryId:{sample_id} incorrectly formatted for genePanel:{gene_panel}")
        raise IncorrectlyFormattedPrimaryId(
            f"Failed to import, primaryId:{sample_id} incorrectly formatted for genePanel:{gene_panel}"
        )

    if not libraries:
        if igocomplete:
            raise ErrorInconsistentDataException(
                f"Failed to fetch SampleManifest for sampleId:{sample_id}. Libraries empty."
            )
        else:
            raise MissingDataException(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Libraries empty.")
    for library in libraries:
        runs = library.get("runs")
        if not runs:
            logger.error(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty.")
            if igocomplete:
                raise ErrorInconsistentDataException(
                    f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty."
                )
            else:
                raise MissingDataException(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty.")
        run_dict = convert_to_dict(runs)
        for run in run_dict.values():
            fastqs = run.get("fastqs")
            if not fastqs:
                logger.error(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Fastqs empty.")
                missing_fastq = True
                run_id = run["runId"] if run["runId"] else "None"
                failed_runs.append(run_id)
                continue
    #         else:
    #             if not redelivery:
    #                 for fastq in fastqs:
    #                     # Check do files exist
    #                     try:
    #                         fastq_location = locate_file(fastq)
    #                     except FailedToLocateTheFileException as e:
    #                         files_unavailable = True
    #                         missing_files.append(fastq)
    #                         continue
    #                     # Check files permissions
    #                     try:
    #                         check_file_permissions(fastq_location)
    #                     except FailedToCopyFilePermissionDeniedException as e:
    #                         permission_error = True
    #                         permission_error_files.append(fastq)
    #                         continue
    #                     # Check is file already registered
    #                     try:
    #                         file_search = File.objects.get(path=fastq_location, file_group=settings.IMPORT_FILE_GROUP)
    #                     except File.DoesNotExist:
    #                         continue
    #                     logger.info("Processing %s" % fastq)
    #                     if file_search:
    #                         conflict = True
    #                         conflict_files.append((file_search.path, str(file_search.id)))
    if missing_fastq:
        raise ErrorInconsistentDataException(
            f"Missing fastq data for igcomplete: {igocomplete} sample {sample_id} : {' '.join(failed_runs)}"
        )
    # if files_unavailable:
    #     raise FailedToLocateTheFileException(f"Missing fastq files for sample {sample_id} {', '.join(missing_files)}")
    # if permission_error:
    #     raise FailedToCopyFilePermissionDeniedException(
    #         f"Failed to access files for sample {sample_id} {', '.join(permission_error_files)}. Bad permissions"
    #     )
    # if not redelivery:
    #     if conflict:
    #         res_str = ""
    #         for f in conflict_files:
    #             res_str += "%s: %s" % (f[0], f[1])
    #         raise ErrorInconsistentDataException(f"Conflict of fastq file(s) {res_str}")


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
    message, path, request_id, file_group_id, file_type, igocomplete, data, library, run, request_metadata, r
):
    try:
        lims_metadata = copy.deepcopy(data)
        library_copy = copy.deepcopy(library)
        lims_metadata[settings.REQUEST_ID_METADATA_KEY] = request_id
        lims_metadata[settings.IGO_COMPLETE_METADATA_KEY] = igocomplete
        lims_metadata["R"] = r
        for k, v in library_copy.items():
            lims_metadata[k] = v
        for k, v in run.items():
            lims_metadata[k] = v
        for k, v in request_metadata.items():
            lims_metadata[k] = v
        metadata = format_metadata(lims_metadata)
        metadata = normalize_metadata(metadata)
    except Exception as e:
        logger.error("Failed to parse metadata for file %s path" % path)
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    try:
        logger.info(metadata)
        # validator.validate(get_metadata_schema().schema)
    except MetadataValidationException as e:
        logger.error("Failed to create file %s. Error %s" % (path, str(e)))
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(e)))
    else:
        recipe = metadata.get(settings.RECIPE_METADATA_KEY, "")
        fastq_location = fix_path_iris(path)
        new_path = CopyService.remap(recipe, fastq_location)  # Get copied file path
        f = FileRepository.filter(path=new_path).first()
        if not f:
            file_object = create_file_object(new_path, file_group_id, metadata, file_type)
        else:
            file_object = f.file
            update_file_object(file_object, f.file.path, metadata)

        if path != new_path:
            CopyService.create_copy_task(message, file_object, fastq_location, new_path)


def format_metadata(original_metadata):
    metadata = copy.deepcopy(original_metadata)
    sample_name = original_metadata.get("cmoSampleName", None)
    sample_class = original_metadata.get(settings.SAMPLE_CLASS_METADATA_KEY, None)
    # ciTag is the new field which needs to be used for the operators
    metadata["ciTag"] = format_sample_name(sample_name, sample_class)
    metadata["sequencingCenter"] = "MSKCC"
    metadata["platform"] = "Illumina"
    return metadata


def normalize_metadata(original_metadata):
    metadata = copy.deepcopy(original_metadata)
    normalizers = initialize_normalizer()
    for n in normalizers:
        metadata = n.normalize(metadata)
    return metadata


def create_file_object(path, file_group, metadata, file_type):
    data = {"path": path, "file_type": file_type, "metadata": metadata, "file_group": file_group}
    serializer = CreateFileSerializer(data=data)
    if serializer.is_valid():
        file = serializer.save()
        return file
    else:
        raise FailedToFetchSampleException("Failed to create file %s. Error %s" % (path, str(serializer.errors)))


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
        file = serializer.save()
    else:
        logger.error("Failed to update file %s: Error %s" % (path, serializer.errors))
        raise FailedToFetchSampleException(
            "Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors)
        )
    return file
