from django.db.models import Prefetch
from file_system.models import File, FileMetadata
from file_system.repository.file_repository import FileRepository
from .make_sample import build_sample, remove_with_caveats
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_samples_from_patient_id(patient_id):
    files = FileRepository.filter(metadata={settings.PATIENT_ID_METADATA_KEY: patient_id})

    data = list()
    for f in files:
        sample = dict()
        sample["id"] = f.file.id
        sample["path"] = f.file.path
        sample["file_name"] = f.file.file_name
        sample["metadata"] = f.metadata
        data.append(sample)

    samples = list()
    # group by igoId
    igo_id_group = dict()
    for sample in data:
        igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
        if igo_id not in igo_id_group:
            igo_id_group[igo_id] = list()
        igo_id_group[igo_id].append(sample)

    for igo_id in igo_id_group:
        samples.append(build_sample(igo_id_group[igo_id]))
    samples, bad_samples = remove_with_caveats(samples)
    if len(bad_samples) > 0:
        logger.warning("Some samples for patient query %s have invalid %i values" % (patient_id, len(bad_samples)))
    return samples
