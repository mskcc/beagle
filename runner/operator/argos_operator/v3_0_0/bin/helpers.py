import os

from django.conf import settings
from django.models import Q

from file_system.repository.file_repository import FileRepository

from .pair_object import PairObj
from .patient_object import PatientObj
from .sample_dmp import SampleDMP
from .sample_igo import SampleIGO
from .sample_pooled_normal import SamplePooledNormal


def get_samples_igo(patient_id, request_id, files_set):
    files = FileRepository.filter(
        queryset=files_set,
        metadata={settings.PATIENT_ID_METADATA_KEY: patient_id, settings.REQUEST_ID_METADATA_KEY: request_id},
    )

    file_list = dict()
    samples = dict()

    for f in files:
        sample_name = f.metadata["ciTag"]
        if sample_name not in file_list:
            file_list[sample_name] = list()
        file_list[sample_name].append(f)

    for sample_name in file_list:
        sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")
        samples[sample_name] = sample_igo

    return samples


def get_samples_dmp(patient_id, bait_set, files_set):
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
    normal = Q(metadata__type="N")
    query = assay & patient & normal
    dmp_bams = FileRepository.filter(queryset=files_set, q=query).order_by("file__file_name")
    samples = list()

    for dmp_bam in dmp_bams:
        bam_meta = dmp_bam.metadata
        samples.append(SampleDMP(bam_meta))

    return samples


def get_samples_pooled_normals(metadata):
    """
    Most logic is already in SamplePooledNormal object, but we can do metadata overrides here
    Required keys:
            settings.PATIENT_ID_METADATA_KEY
            settings.SAMPLE_CLASS_METADATA_KEY
            settings.CMO_SAMPLE_CLASS_METADATA_KEY
            settings.LIBRARY_ID_METADATA_KEY
            settings.BAITSET_METADATA_KEY
            settings.PRESERVATION_METADATA_KEY
            sequencingCenter
            platform
            barcodeIndex
            flowCellId
            runMode
            runId
    """
    return SamplePooledNormal(metadata)


def pair_patient_samples(patient):
    pass


def spoof_barcode(file_path):
    """
    Spoof barcode by removing R1/R2 or .bam from end of filename, reverse the string.
    Works even with compound extensions like .fastq.gz.

    Barcode is used only for submitting to the cluster; makes sure paired fastqs get
    sent together during job distribution
    """
    # Get just the base name
    filename = os.path.basename(file_path)

    # Reverse full filename
    reversed_name = filename[::-1]

    # Remove reversed extensions
    for ext in ["bam", "gz", "fastq", "bz2", "tar"]:
        rev_ext = ext[::-1] + "."  # e.g., 'gz.' to match '.gz'
        if reversed_name.startswith(rev_ext):
            reversed_name = reversed_name[len(rev_ext) :]

    # Remove R1/R2 in reversed form
    reversed_name = reversed_name.replace("1R_", "").replace("2R_", "")

    # Reverse back to get spoofed barcode
    spoofed_barcode = reversed_name[::-1]
    return spoofed_barcode
