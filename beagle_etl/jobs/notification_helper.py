from django.conf import settings
from runner.models import Run
from notifier.tasks import send_notification
from file_system.repository.file_repository import FileRepository
from notifier.events import VoyagerIsProcessingPartialRequestEvent, VoyagerIsProcessingWholeRequestEvent
from notifier.helper import get_emails_to_notify, get_gene_panel, get_number_of_tumor_samples


def _voyager_start_processing(request_id, run_ids, notify=False):
    job_group = settings.BEAGLE_NOTIFIER_EMAIL_GROUP
    sample_ids = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.CMO_SAMPLE_TAG_METADATA_KEY
    )

    runs = Run.objects.filter(id__in=run_ids)
    pipeline = runs.first().app
    # TODO: When this is tested add inform flag to pipeline model
    if str(pipeline.id) not in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_PIPELINES:
        return

    if runs:
        used_samples = set()
        unprocessed_samples = set()
        pooled_normals = 0
        matched_normals = 0

        for run in runs:
            used_samples.add(run.tags.get("sampleNameTumor"))
            used_samples.add(run.tags.get("sampleNameNormal"))
            if "POOLEDNORMAL" in run.tags.get("sampleNameNormal"):
                pooled_normals += 1
            else:
                matched_normals += 1
        for sample in sample_ids:
            if sample not in used_samples:
                investigator_sample_id = FileRepository.filter(
                    metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample},
                    values_metadata=settings.INVESTIGATOR_SAMPLE_ID_METADATA_KEY,
                ).first()
                unprocessed_samples.add(investigator_sample_id)

        gene_panel = get_gene_panel(request_id)
        number_of_samples = get_number_of_tumor_samples(request_id)
        if notify:
            if unprocessed_samples:
                send_to = get_emails_to_notify(request_id, "VoyagerIsProcessingPartialRequestEvent")
                for email in send_to:
                    event = VoyagerIsProcessingPartialRequestEvent(
                        job_notifier=job_group,
                        email_to=email,
                        email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                        subject=f"Confirmation of Project {request_id} running in Pipeline: partial run",
                        request_id=request_id,
                        gene_panel=gene_panel,
                        number_of_samples=len(runs),
                        number_of_samples_received=number_of_samples,
                        match_normal_cnt=matched_normals,
                        pooled_normal_cnt=pooled_normals,
                        unpaired=list(unprocessed_samples),
                    ).to_dict()
                    send_notification.delay(event)
            else:
                send_to = get_emails_to_notify(request_id, "VoyagerIsProcessingWholeRequestEvent")
                for email in send_to:
                    event = VoyagerIsProcessingWholeRequestEvent(
                        job_notifier=job_group,
                        email_to=email,
                        email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                        subject=f"Confirmation of Project {request_id} running in Pipeline",
                        request_id=request_id,
                        gene_panel=gene_panel,
                        number_of_samples=len(runs),
                        number_of_samples_recived=number_of_samples,
                        match_normal_cnt=matched_normals,
                        pooled_normal_cnt=pooled_normals,
                    ).to_dict()
                    send_notification.delay(event)
