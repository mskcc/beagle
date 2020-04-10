from .make_sample import build_sample, remove_with_caveats
from file_system.models import File, FileMetadata
from django.db.models import Prefetch
import logging
logger = logging.getLogger(__name__)


def get_samples_from_patient_id(patient_id):
    file_objs = File.objects.prefetch_related(
        Prefetch('filemetadata_set', queryset=
        FileMetadata.objects.select_related('file').order_by('-created_date'))). \
        order_by('file_name')
    files = file_objs.filter(filemetadata__metadata__patientId=patient_id).all()
    data = list()
    for file in files:
        sample = dict()
        sample['id'] = file.id
        sample['path'] = file.path
        sample['file_name'] = file.file_name
        sample['metadata'] = file.filemetadata_set.first().metadata
        data.append(sample)

    samples = list()
    # group by igoId
    igo_id_group = dict()
    for sample in data:
        igo_id = sample['metadata']['sampleId']
        if igo_id not in igo_id_group:
            igo_id_group[igo_id] = list()
        igo_id_group[igo_id].append(sample)

    for igo_id in igo_id_group:
        samples.append(build_sample(igo_id_group[igo_id]))
    samples, bad_samples = remove_with_caveats(samples)
    if len(bad_samples) > 0:
        logger.warning('BadPatientQuery: %i samples for patient query %s have invalid values' % (len(bad_samples), patient_id))
    return samples
