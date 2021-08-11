"""
Functions for retrieving samples from the database based on other criteria
that wasn't in the operator

For example, get all samples by a patient ID or pooled normals based on the bait set
and preservation type
"""
import logging
import os
from file_system.models import File, FileMetadata, FileGroup
from file_system.repository.file_repository import FileRepository
from django.db.models import Prefetch, Q
from django.conf import settings
from .make_sample import build_sample, remove_with_caveats, format_sample_name
from runner.operator.helper import get_r_orientation, spoof_barcode, init_metadata

LOGGER = logging.getLogger(__name__)


def build_argos_file_groups_query():
    ARGOS_FG_SLUGS = ['lims', 'origin-unknown']
    slug_set = [Q(file__file_group=FileGroup.objects.get(slug=value)) for value in set(ARGOS_FG_SLUGS)]
    query = slug_set.pop()
    for item in slug_set:
        query |= item
    return query


def get_samples_from_patient_id(patient_id):
    """
    Retrieves samples from the database based on the patient_id

    Only retrieve patients from LIMS file group
    """
    all_files = FileRepository.all()
    q_pid = Q(metadata__patientId=patient_id)
    q_fg = build_argos_file_groups_query()
    q = q_pid & q_fg
    files = FileRepository.filter(queryset=all_files, q=q, filter_redact=True)
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


def get_descriptor(bait_set, pooled_normals, preservation_types, run_ids):
    """
    Need descriptor to match pooled normal "recipe", which might need to be re-labeled as bait_set

    Adding correction for IMPACT505 pooled normals
    """
    query = Q(file__file_group=settings.POOLED_NORMAL_FILE_GROUP)
    sample_name = None

    descriptor = None
    for pooled_normal in pooled_normals:
        bset_data = pooled_normal.metadata['recipe']
        if bset_data.lower() in bait_set.lower():
            descriptor = bset_data

    if descriptor: # From returned pooled normals, we found the bait set/recipe we're looking for
        pooled_normals = FileRepository.filter(queryset=pooled_normals, metadata={'recipe': descriptor})

        # sample_name is FROZENPOOLEDNORMAL unless FFPE is in any of the preservation types
        # in preservation_types
        preservations_lower_case = set([x.lower() for x in preservation_types])
        run_ids_suffix_list = [i for i in run_ids if i] # remove empty or false string values
        run_ids_suffix = "_".join(set(run_ids_suffix_list))
        sample_name = "FROZENPOOLEDNORMAL_" + run_ids_suffix
        if "ffpe" in preservations_lower_case:
            sample_name = "FFPEPOOLEDNORMAL_" + run_ids_suffix
    elif "impact505" in bait_set.lower():
        # We didn't find a pooled normal for IMPACT505; return "static" FROZEN or FFPE pool normal
        descriptor = "IMPACT505"
        preservations_lower_case = set([x.lower() for x in preservation_types])
        machine = get_sequencer_type(run_ids)
        if not machine:
            LOGGER.error("Could not find IMPACT505 pooled normal for $s; new machine name?", sample_name)
        if machine is "hiseq":
            sample_name = "FROZENPOOLEDNORMAL_IMPACT505_V1"
            if "ffpe" in preservations_lower_case:
                sample_name = "FFPEPOOLEDNORMAL_IMPACT505_V1"
        if machine is "novaseq":
            sample_name = "FROZENPOOLEDNORMAL_IMPACT505_V2"
            if "ffpe" in preservations_lower_case:
                sample_name = "FFPEPOOLEDNORMAL_IMPACT505_V2"
        q = query & Q(metadata__sampleName=sample_name)
        pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)
        if not pooled_normals:
            LOGGER.error("Could not find IMPACT505 pooled normal to pair %s", sample_name)
    elif "hemepact_v4" in bait_set.lower():
        # We didn't find a pooled normal for HemePACT_v4; return "static" FROZEN or FFPE pool normal
        descriptor = "HemePACT_v4"
        preservations_lower_case = set([x.lower() for x in preservation_types])
        sample_name = "FROZENPOOLEDNORMAL_HemePACT_v4_V1"
        if "ffpe" in preservations_lower_case:
            sample_name = "FFPEPOOLEDNORMAL_HemePACT_v4_V1"
        q = query & Q(metadata__sampleName=sample_name)
        pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)
        if not pooled_normals:
            LOGGER.error("Could not find HemePACT_v4 pooled normal to pair %s", sample_name)

    return pooled_normals, descriptor, sample_name


def get_sequencer_type(run_ids_list):
    hiseq_machines = ['jax', 'pitt']
    novaseq_machines = ['diana', 'michelle', 'aa00227']
    run_ids_lower = [ i.lower() for i in run_ids_list if i ]
    for machine in hiseq_machines:
        is_hiseq = find_substr(machine, run_ids_lower)
        if is_hiseq:
            return "hiseq"
    for machine in novaseq_machines:
        is_novaseq = find_substr(machine, run_ids_lower)
        if is_novaseq:
            return "novaseq"
    return None

def find_substr(s, l):
    return any(s in string for string in l)


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
    pooled_normals, descriptor, sample_name = get_pooled_normal_files(run_ids, preservation_types, bait_set)
    sample_files = list()
    for pooled_normal_file in pooled_normals:
        sample_file = build_pooled_normal_sample_by_file(pooled_normal_file, run_ids, preservation_types, descriptor, sample_name)
        sample_files.append(sample_file)
    pooled_normal = build_sample(sample_files, ignore_sample_formatting=True)

    return pooled_normal


def get_pooled_normal_files(run_ids, preservation_types, bait_set):

    pooled_normals = FileRepository.all()

    query = Q(file__file_group=settings.POOLED_NORMAL_FILE_GROUP)
    run_id_query = build_run_id_query(run_ids)
    preservation_query = build_preservation_query(preservation_types)

    q = query & run_id_query & preservation_query

    pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)

    pooled_normals, descriptor, sample_name = get_descriptor(bait_set, pooled_normals, preservation_types, run_ids)

    return pooled_normals, descriptor, sample_name


def build_pooled_normal_sample_by_file(pooled_normal, run_ids, preservation_types, bait_set, sample_name):
    specimen_type = 'Pooled Normal'
    sample = dict()
    sample['id'] = pooled_normal.file.id
    sample['path'] = pooled_normal.file.path
    sample['file_name'] = pooled_normal.file.file_name
    metadata = init_metadata()
    metadata['sampleId'] = sample_name
    metadata['sampleName'] = sample_name
    metadata['cmoSampleName'] = sample_name
    metadata['requestId'] = sample_name
    metadata['sequencingCenter'] = "MSKCC"
    metadata['platform'] = "Illumina"
    metadata['baitSet'] = bait_set 
    metadata['recipe'] = bait_set
    metadata['runId'] = run_ids
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
    metadata['runMode'] = ""
    metadata['sampleClass'] = ""
    sample['metadata'] = metadata
    return sample


def get_dmp_bam(patient_id, bait_set, tumor_type):
    """
    From a patient id and bait set, get matching dmp bam normal
    """
    file_objs = FileRepository.all()

    dmp_query = build_dmp_query(patient_id, bait_set)

    dmp_bam = FileRepository.filter(queryset=file_objs, q=dmp_query).order_by('file__file_name').first()

    if dmp_bam:
        sample = build_dmp_sample(dmp_bam, patient_id, bait_set, tumor_type)
        built_sample = build_sample([sample], ignore_sample_formatting=True)
        return built_sample
    return None


def build_dmp_sample(dmp_bam, patient_id, bait_set, tumor_type):
    
    dmp_metadata = dmp_bam.metadata
    specimen_type = "DMP"
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
    metadata['cmoSampleName'] = metadata['sampleName']
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
    metadata['tumorOrNormal'] = tumor_type
    metadata['patientId'] = patient_id
    metadata['specimenType'] = specimen_type
    metadata['runMode'] = ""
    metadata['sampleClass'] = ""
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
    if "impact505" in bait_set.lower():
        value = "IMPACT505"
    assay = Q(metadata__cmo_assay=value)
    # formatting to look like CMO patient IDs in dmp2cmo
    if "C-" in patient_id[:2]:
      patient_id = patient_id[2:]
    patient = Q(metadata__patient__cmo=patient_id)
    normal = Q(metadata__type='N')
    query = assay & patient & normal
    return query
