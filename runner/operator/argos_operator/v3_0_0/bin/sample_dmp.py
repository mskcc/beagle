from django.conf import settings
from django.db.models import Q

from file_system.repository.file_repository import FileRepository

from ..utils.barcode_utils import spoof_barcode
from .files_object import FilesObj
from .sample_file_object import SampleFile

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.PATIENT_ID_METADATA_KEY,
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.CMO_SAMPLE_TAG_METADATA_KEY,  # ciTag
    settings.LIBRARY_ID_METADATA_KEY,
    settings.BAITSET_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
]


class SampleDMP:
    def __init__(self, metadata):
        self.metadata = {k: metadata[k] for k in REQUIRED_KEYS if k in metadata}
        patient_id = self.metadata[settings.PATIENT_ID_METADATA_KEY]
        bait_set = self.metadata[settings.BAITSET_METADATA_KEY]
        self.tumor_type = self.__get_tumor_type__()
        dmp_bam = self.__get_dmp_bam__(patient_id, bait_set)
        self.metadata["barcodeIndex"] = spoof_barcode(dmp_bam.file.path)
        self.sample_file = SampleFile(dmp_bam.file.path, self.metadata)

    def __get_dmp_bam__(self, patient_id, bait_set):
        """
        From a patient id and bait set, get matching dmp bam
        """
        file_objs = FileRepository.all()
        dmp_query = self.__build_dmp_query__(patient_id, bait_set)
        dmp_bam = FileRepository.filter(queryset=file_objs, q=dmp_query).order_by("file__file_name").first()

        return dmp_bam

    def __build_dmp_query__(self, patient_id, bait_set):
        """
        Build simple Q queries for patient id, bait set, and type 'N' to signify "normal"

        The bait set from file groups/LIMS is different from what's in DMP, so this
        translates it.

        Patient ID in DMP also doesn't contain C-, so this removes that prefix
        """
        value = ""
        if "impact341" in bait_set.lower():
            value = "IMPACT341"
        if "impact410" in bait_set.lower():
            value = "IMPACT410"
        if "impact468" in bait_set.lower():
            value = "IMPACT468"
        if "hemepact_v4" in bait_set.lower():
            value = "HEMEPACT"
        if "impact505" in bait_set.lower():
            value = "IMPACT505"
        assay = Q(metadata__cmo_assay=value)
        # formatting to look like CMO patient IDs in dmp2cmo
        if "C-" in patient_id[:2]:
            patient_id = patient_id[2:]
        patient = Q(metadata__patient__cmo=patient_id)
        normal = Q(metadata__type=self.tumor_type)
        query = assay & patient & normal
        return query

    def __get_tumor_type__(self):
        v = self.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
        if v and "normal" in v:
            return "N"
        return "T"

    def __repr__(self):
        return f"SampleDMP(Sample=({self.sample_file}))"
