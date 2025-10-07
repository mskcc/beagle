"""
SampleDMP object

Purpose of this object is to convert incoming metadata - usually from a Tumor sample - and find all DMP samples
associated with the patient_id and bait_set.

From this information, we then take that incoming metadata, combine them with the retrieved DMP sample, and create files/objects
that then can be submitted as input for the ARGOS pipeline
"""

import copy
from pprint import pprint

from django.conf import settings
from django.db.models import Q

from file_system.repository.file_repository import FileRepository

from ..utils.barcode_utils import spoof_barcode
from .files_object import FilesObj
from .sample_file_object import SampleFile

RESET_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.CMO_SAMPLE_TAG_METADATA_KEY,  # ciTag
]

REQUIRED_KEYS = [
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.PATIENT_ID_METADATA_KEY,
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.LIBRARY_ID_METADATA_KEY,
    settings.BAITSET_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
]


class SampleDMPManager:
    def __init__(self, metadata_src):
        self.metadata = dict.fromkeys(RESET_KEYS + REQUIRED_KEYS, None)  # initialize empty array
        self.metadata = {
            k: metadata_src[k] for k in REQUIRED_KEYS if k in metadata_src
        }  # checkpointing metadata we will be assigning to dmp bam
        patient_id = self.metadata[settings.PATIENT_ID_METADATA_KEY]
        bait_set = self.metadata[settings.BAITSET_METADATA_KEY]
        self.all_dmp_bams = []
        self.sample_file = None

        dmp_bam, dmp_bams_all = self.__get_dmp_bam__(patient_id, bait_set)
        if dmp_bam:
            dmp_bam_metadata = self.__map_metadata__(dmp_bam)
            sample_file = SampleFile(dmp_bam.file.path, dmp_bam_metadata)  # this is the one true dmp bam
            sample_name = dmp_bam_metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
            self.dmp_bam_normal = SampleDMP(sample_name, dmp_bam_metadata)
            self.dmp_bam_normal.add_sample_file(sample_file)

        if dmp_bams_all:
            for f in dmp_bams_all:
                dmp_bam_metadata = self.__map_metadata__(f)
                sample_file = SampleFile(
                    f.file.path, dmp_bam_metadata
                )  # likely only one, but here to grab and refer to all if it's around
                sample_name = dmp_bam_metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
                dmp_bam_this = SampleDMP(sample_name, dmp_bam_metadata)
                self.all_dmp_bams.append(dmp_bam_this)

    def __map_metadata__(self, dmp_bam):
        bam_meta = dmp_bam.metadata
        dmp_bam_metadata = copy.deepcopy(self.metadata)
        dmp_bam_metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = bam_meta["external_id"]
        dmp_bam_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = bam_meta["external_id"]
        dmp_bam_metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = "Normal" if "N" in bam_meta["type"] else "Tumor"
        dmp_bam_metadata["barcodeIndex"] = spoof_barcode(dmp_bam.file.path)
        return dmp_bam_metadata

    def __get_dmp_bam__(self, patient_id, bait_set):
        """
        From a patient id and bait set, get matching dmp bam
        """
        file_objs = FileRepository.all()
        dmp_query = self.__build_dmp_query__(patient_id, bait_set)
        dmp_query_normal = self.__add_dmp_query_normal__(dmp_query)
        dmp_bams_all = FileRepository.filter(queryset=file_objs, q=dmp_query).order_by("file__file_name")
        dmp_bam = FileRepository.filter(queryset=file_objs, q=dmp_query_normal).order_by("file__file_name").first()
        if not dmp_bam:
            print("No dmp_bam found; query %s" % dmp_query_normal)

        return dmp_bam, dmp_bams_all

    def __add_dmp_query_normal__(self, query):
        normal = Q(metadata__type="N")
        query_normal = query & normal
        return query_normal

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
        query = assay & patient
        return query

    def __get_tumor_type__(self):
        v = self.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
        if v and "normal" in v:
            return "N"
        return "T"


class SampleDMP:
    def __init__(self, sample_name, metadata):
        self.sample_name = sample_name
        self.metadata = metadata
        self.sample_files = []

    def add_sample_file(self, sample_file):
        self.sample_files.append(sample_file)

    def __repr__(self):
        return f"SampleDMP(Sample=({self.sample_files}))"
