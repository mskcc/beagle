from django.conf import settings
from file_system.models import Patient
from file_system.repository import FileRepository


def populate_patient_samples():
    from_lims = FileRepository.filter(file_group=settings.IMPORT_FILE_GROUP, values_metadata="cmoPatientId").all()
    for p in Patient.objects.filter(patient_id__in=from_lims).all():
        samples = FileRepository.filter(metadata={"cmoPatientId": p.patient_id}, values_metadata="primaryId").all()
        p.samples = list(samples)
        p.save()
