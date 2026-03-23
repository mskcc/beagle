from django.conf import settings
from notifier.events import (
    ETLImportEvent,
    ETLJobsLinksEvent,
)
from notifier.tasks import send_notification
from file_system.repository import FileRepository


def generate_ticket_description(request_id, job_group_id, job_group_notifier_id, sample_list, request_metadata):
    cnt_samples_completed = 0
    cnt_samples_failed = 0
    for job in sample_list:
        if job["status"] == "COMPLETED":
            cnt_samples_completed += 1
        elif job["status"] == "FAILED":
            cnt_samples_failed += 1

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
        data_access_emails,
        other_contact_emails,
    )
    e = event.to_dict()
    send_notification.delay(e)

    etl_event = ETLJobsLinksEvent(job_group_notifier_id, request_id, sample_list)
    etl_e = etl_event.to_dict()
    send_notification.delay(etl_e)
