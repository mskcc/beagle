from django.conf import settings
from notifier.events import (
    ETLImportEvent,
    ETLJobsLinksEvent,
)
from runner.models import Run
from notifier.tasks import send_notification
from file_system.repository.file_repository import FileRepository
from notifier.events import VoyagerIsProcessingPartialRequestEvent, \
    VoyagerIsProcessingWholeRequestEvent, \
    VoyagerCantProcessRequestAllNormalsEvent


def _voyager_start_processing(request_id, runs):
    job_group = settings.BEAGLE_NOTIFIER_EMAIL_GROUP
    sample_ids = FileRepository.objects.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
                                               values_metadata=settings.SAMPLE_ID_METADATA_KEY)
    investigator_email = FileRepository.objects.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
                                                       values_metadata='investigatorEmail').first()
    lab_head_email = FileRepository.objects.filter(metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
                                                   values_metadata='labHeadEmail').first()
    sent_to = settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO
    if investigator_email not in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_BLACKLIST:
        sent_to.add(investigator_email)
    if lab_head_email not in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_BLACKLIST:
        sent_to.add(lab_head_email)

    if not runs:
        for email in sent_to:
            event = VoyagerCantProcessRequestAllNormalsEvent(job_notifier=job_group,
                                                             email_to=email,
                                                             email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                                                             subject="Voyager Status",
                                                             content="All Normals").to_dict()
            send_notification.delay(event)

    else:
        used_samples = set()
        unprocessed_samples = set()

        for run in runs:
            used_samples.add(run.tags.get("sampleNameTumor"))
            used_samples.add(run.tags.get("sampleNameNormal"))
        for sample in sample_ids:
            if sample not in used_samples:
                unprocessed_samples.add(sample)

        if unprocessed_samples:
            for email in sent_to:
                event = VoyagerIsProcessingPartialRequestEvent(job_notifier=job_group,
                                                               email_to=email,
                                                               email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                                                               subject="Voyager Status",
                                                               content=unprocessed_samples).to_dict()
                send_notification.delay(event)
        else:
            for email in sent_to:
                event = VoyagerIsProcessingWholeRequestEvent(job_notifier=job_group,
                                                             email_to=email,
                                                             email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                                                             subject="Voyager Status",
                                                             content=request_id).to_dict()
                send_notification.delay(event)


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
