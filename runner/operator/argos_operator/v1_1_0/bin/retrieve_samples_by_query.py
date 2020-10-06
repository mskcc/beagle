"""
Functions for retrieving samples from the database based on other criteria
that wasn't in the operator

For example, get all samples by a patient ID or pooled normals based on the bait set
and preservation type
"""
import logging
import os
from file_system.models import File, FileMetadata
from file_system.repository.file_repository import FileRepository
from django.db.models import Prefetch, Q
from django.conf import settings
from .make_sample import build_sample, remove_with_caveats, format_sample_name

LOGGER = logging.getLogger(__name__)


def get_samples_from_patient_id(patient_id):
    """
    Retrieves samples from the database based on the patient_id
    """
    files = FileRepository.filter(metadata={"patientId": patient_id})
    data = list()
    for current_file in files:
        sample = dict()
        sample['id'] = current_file.file.id
        sample['path'] = current_file.file.path
        sample['file_name'] = current_file.file.file_name
        sample['metadata'] = current_file.metadata
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
    number_of_bad_samples = len(bad_samples)
    if number_of_bad_samples > 0:
        LOGGER.warning('Some samples for patient query %s have invalid %i values',
                       patient_id, number_of_bad_samples)
    return samples


def get_descriptor(bait_set, pooled_normals):
    """
    Need descriptor to match pooled normal "recipe", which might need to be re-labeled as bait_set
    """
    for pooled_normal in pooled_normals:
        descriptor = pooled_normal.metadata['recipe']
        if descriptor.lower() in bait_set.lower():
            return descriptor
    return None


def build_run_id_query(data):
    """
    Build complex Q object run id query from given data

    Only does OR queries, as seen in line

       query |= item

    Very similar to build_preservation_query, but "filemetadata__metadata__runId"
    can't be sent as a value, so had to make a semi-redundant function
    """
    data_query_set = [Q(metadata__runId=value) for value in set(data)]
    query = data_query_set.pop()
    for item in data_query_set:
        query |= item
    return query


def build_preservation_query(data):
    """
    Build simple query for either FROZEN or FFPE pooled normal

    Main logic: if FFPE in data, return FFPE query; else, return FROZEN query
    """
    preservations_lower_case = set([x.lower() for x in data])
    value = "FROZEN"
    if "ffpe" in preservations_lower_case:
        value = "FFPE"
    # case-insensitive matching
    query = Q(metadata__preservation__iexact=value)
    return query


def get_pooled_normals(run_ids, preservation_types, bait_set):
    """
    From a list of run_ids, preservation types, and bait sets, get all potential pooled normals
    """
    pooled_normals = FileRepository.all()

    query = Q(file__file_group=settings.POOLED_NORMAL_FILE_GROUP)
    run_id_query = build_run_id_query(run_ids)
    preservation_query = build_preservation_query(preservation_types)

    q = query & run_id_query & preservation_query

    pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)

    descriptor = get_descriptor(bait_set, pooled_normals)

    if descriptor: # From returned pooled normals, we found the bait set/recipe we're looking for
        pooled_normals = FileRepository.filter(queryset=pooled_normals, metadata={'recipe': descriptor})

        # sample_name is FROZENPOOLEDNORMAL unless FFPE is in any of the preservation types
        # in preservation_types
        preservations_lower_case = set([x.lower() for x in preservation_types])
        run_ids_suffix_list = [i for i in run_ids if i] # remove empty or false string values
        run_ids_suffix = "_".join(run_ids_suffix_list)
        sample_name = "FROZENPOOLEDNORMAL_" + run_ids_suffix
        if "ffpe" in preservations_lower_case:
            sample_name = "FFPEPOOLEDNORMAL_" + run_ids_suffix
    elif "impact505" in bait_set.lower():
        # We didn't find a pooled normal for IMPACT505; return "static" FROZEN or FFPE pool normal
        preservations_lower_case = set([x.lower() for x in preservation_types])
        sample_name = "FROZENPOOLEDNORMAL_IMPACT505_V1"
        if "ffpe" in preservations_lower_case:
            sample_name = "FFPEPOOLEDNORMAL_IMPACT505_V1"
        q = query & Q(metadata__sampleName=sample_name)
        pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)
        if not pooled_normals:
            LOGGER.error("Could not find IMPACT505 pooled normal to pair %s", sample_name)
            return None
    else:
        return None

    specimen_type = 'Pooled Normal'

    sample_files = list()

    if len(pooled_normals) > 0:
        for pooled_normal in pooled_normals:
            sample = dict()
            sample['id'] = pooled_normal.file.id
            sample['path'] = pooled_normal.file.path
            sample['file_name'] = pooled_normal.file.file_name
            metadata = init_metadata()
            metadata['sampleId'] = sample_name
            metadata['sampleName'] = sample_name
            metadata['requestId'] = sample_name
            metadata['sequencingCenter'] = "MSKCC"
            metadata['platform'] = "Illumina"
            metadata['baitSet'] = descriptor
            metadata['recipe'] = descriptor
            metadata['run_id'] = run_ids
            metadata['preservation'] = preservation_types
            metadata['libraryId'] = sample_name + "_1"
            # because rgid depends on flowCellId and barcodeIndex, we will
            # spoof barcodeIndex so that pairing can work properly; see
            # build_sample in runner.operator.argos_operator.bin
            metadata['R'] = get_r_orientation(pooled_normal.file.file_name)
            metadata['barcodeIndex'] = spoof_barcode(sample['file_name'], metadata['R'])
            metadata['flowCellId'] = 'PN_FCID'
            metadata['tumorOrNormal'] = 'Normal'
            metadata['patientId'] = 'PN_PATIENT_ID'
            metadata['specimenType'] = specimen_type
            sample['metadata'] = metadata
            sample_files.append(sample)
        pooled_normal = build_sample(sample_files, ignore_sample_formatting=True)
        return pooled_normal
    return None


def get_dmp_normal(patient_id, bait_set):
    """
    From a patient id and bait set, get matching dmp bam normal
    """
    file_objs = FileRepository.all()

    dmp_query = build_dmp_query(patient_id, bait_set)

    dmp_bam = FileRepository.filter(queryset=file_objs, q=dmp_query).order_by('file__file_name').first()

    if dmp_bam:
        sample = build_dmp_sample(dmp_bam, patient_id, bait_set)
        built_sample = build_sample([sample], ignore_sample_formatting=True)
        return built_sample
    return None


def build_dmp_sample(dmp_bam, patient,_id, bait_set):
    dmp_metadata = dmp_bam.metadata
    specimen_type = "DMP Normal"
    sample_name = dmp_metadata['external_id']
    sequencingCenter = "MSKCC"
    platform = "Illumina"
    sample = dict()
    sample['id'] = dmp_bam.file.id
    sample['path'] = dmp_bam.file.path
    sample['file_name'] = dmp_bam.file.file_name
    sample['file_type'] = dmp_bam.file.file_type
    metadata = init_metadata()
    metadata['sampleId'] = sample_name
    metadata['sampleName'] = format_sample_name(sample_name, specimen_type)
    metadata['requestId'] = sample_name
    metadata['sequencingCenter'] = sequencingCenter
    metadata['platform'] = platform
    metadata['baitSet'] = bait_set
    metadata['recipe'] = bait_set
    metadata['run_id'] = ""
    metadata['preservation'] = ""
    metadata['libraryId'] = sample_name + "_1"
    metadata['R'] = 'Not applicable'
    # because rgid depends on flowCellId and barcodeIndex, we will
    # spoof barcodeIndex so that pairing can work properly; see
    # build_sample in runner.operator.argos_operator.bin
    metadata['barcodeIndex'] = 'DMP_BARCODEIDX'
    metadata['flowCellId'] = 'DMP_FCID'
    metadata['tumorOrNormal'] = 'Normal'
    metadata['patientId'] = patient_id
    metadata['specimenType'] = specimen_type
    sample['metadata'] = metadata
    return sample


def build_dmp_query(patient_id, bait_set):
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
    assay = Q(metadata__cmo_assay=value)
    patient = Q(metadata__patient__cmo=patient_id.lstrip('C-'))
    normal = Q(metadata__type='N')
    query = assay & patient & normal
    return query


def get_r_orientation(fastq_filename):
    """
    Retrieve R orientation of fastq filename
    """
    reversed_filename = ''.join(reversed(fastq_filename))
    r1_idx = reversed_filename.find('1R')
    r2_idx = reversed_filename.find('2R')
    if r1_idx == -1 and r2_idx == -1:
        return "ERROR"
    elif r1_idx > 0 and r2_idx == -1:
        return "R1"
    elif r2_idx > 0 and r1_idx == -1:
        return 'R2'
    elif r1_idx > 0 and r2_idx > 0:
        if r1_idx < r2_idx:
            return 'R1'
        return 'R2'
    return 'ERROR'


def spoof_barcode(sample_file_name, r_orientation):
    """
    Spoof barcode by removing 'R1' or 'R2' from the filename; paired fastqs
    are assumed to have only these two values as different

    We are also assuming there are no periods in the file names other than extensions
    """
    reversed_str = ''.join(reversed(sample_file_name))
    if r_orientation == 'R1':
        reversed_str = reversed_str.replace('1R', '')
    else:
        reversed_str = reversed_str.replace('2R', '')
    reversed_str = ''.join(reversed(reversed_str))
    spoofed_barcode = reversed_str.split(os.extsep)[0]
    return spoofed_barcode


def init_metadata():
    """
    Build a fastq dictionary containing expected metadata for a sample

    This just instantiates it.
    """
    metadata = dict()
    metadata['requestId'] = ""
    metadata['sampleId'] = ""
    metadata['libraryId'] = ""
    metadata['baitSet'] = ""
    metadata['tumorOrNormal'] = ""
    metadata['specimenType'] = ""
    metadata['species'] = ""
    metadata['sampleName'] = ""
    metadata['flowCellId'] = ""
    metadata['barcodeIndex'] = ""
    metadata['patientId'] = ""
    metadata['runDate'] = ""
    metadata['R'] = ""
    metadata['labHeadName'] = ""
    metadata['labHeadEmail'] = ""
    metadata['runId'] = ""
    metadata['preservation'] = ""
    return metadata
