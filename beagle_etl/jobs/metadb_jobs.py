import copy
import json
import logging

from deepdiff import DeepDiff
from datetime import datetime, timedelta
from dateutil.parser import parse
from celery import shared_task
from django.conf import settings
from beagle_etl.smile_message.objects.request_object import RequestMetadata
from beagle_etl.smile_message.objects.update_request import UpdateRequest
from beagle_etl.smile_message.objects.update_sample import UpdateSample
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
from notifier.tasks import send_notification
from notifier.helper import get_emails_to_notify
from beagle_etl.models import Operator, ETLConfiguration, SMILEMessage, RequestCallbackJob, RequestCallbackJobStatus
from file_system.serializers import UpdateFileSerializer
from file_system.repository.file_repository import FileRepository
from file_system.models import File
from beagle_etl.exceptions import (
    FailedToSubmitToOperatorException,
    FailedToRegisterFileException,
    FailedToFetchRequestMetadata,
    ETLExceptions,
)

from runner.tasks import create_jobs_from_request
from file_system.serializers import CreateFileSerializer
from beagle_etl.jobs.helper_jobs import fix_path_iris, calculate_checksum
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


def normalize_fastq_value(val):
    if isinstance(val, list):
        return set(val)
    elif isinstance(val, str):
        return {val}
    else:
        return set()


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


def fetch_request_metadata(request_id):
    file_example = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, file_group=settings.IMPORT_FILE_GROUP
    ).first()
    if file_example:
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
    else:
        raise FailedToFetchRequestMetadata(f"No files for {request_id} previously imported")


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
    # TODO: New Request Completed
    message = SMILEMessage.objects.get(id=message_id)

    try:
        data = RequestMetadata.from_dict(json.loads(message.message))
    except Exception as e:
        message.add_log(str(e))
        message.failed()
        return

    if not data.isCmoRequest:
        # Non CmoRequests not supported
        logger.info(f"Request {data.igoRequestId} is not CMO Request")
        message.add_log(f"Request {data.igoRequestId} is not CMO Request")
        message.not_supported()
        return

    logger.info(f"Importing new request: {data.igoRequestId} with genePanel: {data.genePanel}\n")
    message.add_log(f"Importing new request: {data.igoRequestId} with genePanel: {data.genePanel}")

    # Validate samples and fastqs
    log, status = data.validate_all_samples()
    message.add_log(log)

    jgn_id = None
    if message.job_group_notifier:
        jgn_id = str(message.job_group_notifier.id)

    set_recipe_event = ETLSetRecipeEvent(jgn_id, data.genePanel).to_dict()
    send_notification.delay(set_recipe_event)

    study, _ = Study.objects.get_or_create(study_id=StudyObject.generate_study_id(data.labHeadName))

    valid_samples = {k for k, v in status.items() if v.status == "COMPLETED"}
    request_metadata = data.request_metadata()

    import_status = True
    for sample in data.samples:
        if sample.primaryId in valid_samples:
            for library in sample.libraries:
                for run in library.runs:
                    for fastq in run.fastqs:
                        sample_metadata = sample.sample_metadata(library, run, fastq)
                        metadata = copy.deepcopy(request_metadata)
                        metadata.update(sample_metadata)
                        fastq_location = fix_path_iris(fastq)
                        try:
                            file_obj = create_or_update_file(fastq_location, metadata)
                        except FailedToRegisterFileException as e:
                            logger.error(f"Failed to register file {fastq_location}")
                            message.add_log(f"Failed to register file {fastq_location}")
                            # Update sample status
                            status[sample.primaryId].status = "FAILED"
                            status[sample.primaryId].message += f"{str(e)}\n"
                            import_status = False
                        else:
                            sample_objs = file_obj.get_samples()
                            request_obj = file_obj.get_request()
                            if sample_objs:
                                [study.samples.add(sample_obj) for sample_obj in sample_objs]
                            if request_obj:
                                study.requests.add(request_obj)

    sample_status = sorted([sample.to_dict() for sample in status.values()], key=lambda d: d["sample"])
    message.set_sample_status(sample_status)
    # TODO: Check is this logic ok
    message.complete(request_metadata) if import_status else message.failed(request_metadata)

    fastq_metadata = fetch_fastq_metadata(data.igoRequestId)
    create_request_callback_instance(
        data.igoRequestId,
        message,
        data.genePanel,
        sample_status,
        message.job_group,
        message.job_group_notifier,
        fastq_metadata=fastq_metadata,
    )


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
def update_request_job(message_id):
    message = SMILEMessage.objects.get(id=message_id)
    try:
        data = UpdateRequest.from_list(json.loads(message.message))
    except Exception as e:
        message.add_log(str(e))
        message.failed()
        return

    request_update = data.get_latest_update().requestMetadataJson

    # List all files to update
    files = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_update.igoRequestId}, file_group=settings.IMPORT_FILE_GROUP
    )

    jgn_id = None
    if message.job_group_notifier:
        jgn_id = str(message.job_group_notifier.id)

    redelivery_event = RedeliveryEvent(jgn_id).to_dict()
    send_notification.delay(redelivery_event)

    sample_status = dict()
    failed_samples = []
    for f in files:
        new_metadata = copy.deepcopy(f.metadata)
        new_metadata.update(request_update.request_metadata())
        try:
            update_file_object(f.file, f.file.path, new_metadata)
        except FailedToRegisterFileException as e:
            failed_samples.append(f.metadata[settings.SAMPLE_ID_METADATA_KEY])

        if f.metadata[settings.SAMPLE_ID_METADATA_KEY] not in sample_status.keys():
            status = "FAILED" if f.metadata[settings.SAMPLE_ID_METADATA_KEY] in failed_samples else "COMPLETED"
            status = {
                "type": "SAMPLE",
                "igocomplete": f.metadata[settings.IGO_COMPLETE_METADATA_KEY],
                "sample": f.metadata[settings.SAMPLE_ID_METADATA_KEY],
                "status": status,
                "message": f"Files for {f.metadata[settings.SAMPLE_ID_METADATA_KEY]} updated",
                "code": None,
            }
            sample_status[f.metadata[settings.SAMPLE_ID_METADATA_KEY]] = status

    sample_status = sorted([sample for sample in sample_status.values()], key=lambda d: d["sample"])
    message.set_sample_status(sample_status)
    message.complete(request_update)


@shared_task
def update_sample_job(message_id):
    message = SMILEMessage.objects.get(id=message_id)
    try:
        data = UpdateSample.from_dict(json.loads(message.message))
    except ETLExceptions as e:
        message.add_log(str(e))
        message.failed()
        return

    if not data.latestSampleMetadata.is_cmo_sample():
        # Non CMO samples not supported
        logger.info(f"Sample {data.latestSampleMetadata.primaryId} is not a CMO sample")
        message.add_log(f"Sample {data.latestSampleMetadata.primaryId} is not a CMO sample")
        message.not_supported()
        return

    log, sample_status = data.latestSampleMetadata.validate_with_file_checks(redelivery=True)
    message.add_log(log)

    if sample_status.status != "COMPLETED":
        message.failed()
        return

    jgn_id = None
    if message.job_group_notifier:
        jgn_id = str(message.job_group_notifier.id)

    new_paths = []
    files = FileRepository.filter(
        metadata={settings.SAMPLE_ID_METADATA_KEY: data.latestSampleMetadata.primaryId},
        file_group=settings.IMPORT_FILE_GROUP,
    ).all()
    file_paths = [file_obj.file.original_path for file_obj in files]

    if not files:
        error_message = f"No files registered {data.latestSampleMetadata.primaryId}. Update Sample Job Failed"
        logger.warning(error_message)
        message.add_log(error_message)
        message.failed()
        return

    redelivery_event = RedeliveryEvent(jgn_id).to_dict()
    send_notification.delay(redelivery_event)

    request_metadata = fetch_request_metadata(data.latestSampleMetadata.igoRequestId)

    update_completed = True
    for library in data.latestSampleMetadata.libraries:
        for run in library.runs:
            for fastq in run.fastqs:
                metadata = copy.deepcopy(request_metadata)
                sample_metadata = data.latestSampleMetadata.sample_metadata(library, run, fastq)
                metadata.update(sample_metadata)
                fastq_location = fix_path_iris(fastq)
                try:
                    file_obj = create_or_update_file(fastq_location, metadata)
                    new_paths.append(fastq_location)
                except FailedToRegisterFileException as e:
                    update_completed = False
                    update_file_error_message = f"Failed to register file {fastq_location}"
                    message.add_log(update_file_error_message)
                    logger.error(update_file_error_message)
                    sample_status.status = "FAILED"
                    sample_status.message += f"{str(e)}\n"

    message.set_sample_status(sample_status.to_dict())
    # Remove unnecessary files
    files_to_remove = set(file_paths) - set(new_paths)
    for fi in list(files_to_remove):
        file_removed_message = f"File {fi} removed from the Sample"
        message.add_log(file_removed_message)
        logger.warning(file_removed_message)
        File.objects.filter(path=fi, file_group_id=settings.IMPORT_FILE_GROUP).delete()
    message.complete(request_metadata) if update_completed else message.failed(request_metadata)


def create_or_update_file(path, metadata, file_group=None, file_type="fastq"):
    if file_group is None:
        file_group = settings.IMPORT_FILE_GROUP
    file_obj = File.objects.filter(original_path=path, file_group=file_group).first()
    if not file_obj:
        return create_file_object(path, file_group, metadata, file_type)
    else:
        return update_file_object(file_obj, path, metadata)


def create_file_object(path, file_group, metadata, file_type):
    data = {"path": path, "file_type": file_type, "metadata": metadata, "file_group": file_group}
    serializer = CreateFileSerializer(data=data)
    if serializer.is_valid():
        file = serializer.save()
        calculate_checksum.delay(str(file.id))
        return file
    else:
        raise FailedToRegisterFileException("Failed to create file %s. Error %s" % (path, str(serializer.errors)))


def update_file_object(file_object, path, metadata, job_group_notifier=None):
    file_ = FileRepository.get(file_object.id)
    ddiff = DeepDiff(file_.metadata, metadata, ignore_order=True)
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
        raise FailedToRegisterFileException(
            "Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors)
        )
    diff_file_name = "%s_metadata_update_%s.json" % (file_.file.file_name, file_.version + 1)
    msg = "Updating file metadata: %s, details in file %s\n" % (file_.file.path, diff_file_name)
    update = RedeliveryUpdateEvent(job_group_notifier, msg).to_dict()
    diff_details_event = LocalStoreFileEvent(job_group_notifier, diff_file_name, str(ddiff)).to_dict()
    send_notification.delay(update)
    send_notification.delay(diff_details_event)
    return file
