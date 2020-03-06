"""
Functions for retrieving samples from the database based on other criteria
that wasn't in the operator

For example, get all samples by a patient ID or pooled normals based on the bait set
and preservation type
"""
import logging
import os
from file_system.models import File, FileMetadata
from django.db.models import Prefetch, Q
from django.conf import settings
from .make_sample import build_sample, remove_with_caveats

LOGGER = logging.getLogger(__name__)


def get_samples_from_patient_id(patient_id):
    """
    Retrieves samples from the database based on the patient_id
    """
    file_objs = File.objects.prefetch_related(
        Prefetch('filemetadata_set', queryset=
                 FileMetadata.objects.select_related('file').order_by('-created_date'))).\
                 order_by('file_name')
    files = file_objs.filter(filemetadata__metadata__patientId=patient_id).all()
    data = list()
    for current_file in files:
        sample = dict()
        sample['id'] = current_file.id
        sample['path'] = current_file.path
        sample['file_name'] = current_file.file_name
        sample['metadata'] = current_file.filemetadata_set.first().metadata
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
        descriptor = pooled_normal.filemetadata_set.first().metadata['recipe']
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
    data_query_set = [Q(filemetadata__metadata__runId=value) for value in set(data)]
    query = data_query_set.pop()
    for item in data_query_set:
        query |= item
    return query


def build_preservation_query(data):
    """
    Build complex Q object preservation type query from given data

    Only does OR queries, as seen in line

       query |= item

    Very similar to build_run_id_query, but "filemetadata__metadata__preservation"
    can't be sent as a value, so had to make a semi-redundant function
    """
    data_query_set = [Q(filemetadata__metadata__preservation=value) for value in set(data)]
    query = data_query_set.pop()
    for item in data_query_set:
        query |= item
    return query


def get_pooled_normals(run_ids, preservation_types, bait_set):
    """
    From a list of run_ids, preservation types, and bait sets, get all potential pooled normals
    """
    file_objs = File.objects.prefetch_related(
        Prefetch('filemetadata_set', queryset=FileMetadata.objects.select_related('file').\
            order_by('-created_date')))
    query = Q(file_group=settings.POOLED_NORMAL_FILE_GROUP)
    run_id_query = Q()
    preservation_query = Q()

    run_id_query = build_run_id_query(run_ids)
    preservation_query = build_preservation_query(preservation_types)
    pooled_normals = file_objs.\
        filter(query & run_id_query & preservation_query).\
        order_by('file_name')
    descriptor = get_descriptor(bait_set, pooled_normals)

    if not descriptor: # i.e., no pooled normal
        return None
    pooled_normals = pooled_normals.filter(filemetadata__metadata__recipe=descriptor)
    sample_files = list()

    # arbitrarily named
    sample_name = "pooled_normal_%s_%s_%s" % (descriptor,
                                              "_".join(run_ids),
                                              "_".join(preservation_types))

    num_of_pooled_normals = len(pooled_normals)
    if num_of_pooled_normals > 0:
        for pooled_normal in pooled_normals:
            sample = dict()
            sample['id'] = pooled_normal.id
            sample['path'] = pooled_normal.path
            sample['file_name'] = pooled_normal.file_name
            metadata = init_metadata()
            metadata['sampleId'] = sample_name
            metadata['sampleName'] = sample_name
            metadata['requestId'] = sample_name
            metadata['baitSet'] = descriptor
            metadata['recipe'] = descriptor
            metadata['run_id'] = run_ids
            metadata['preservation'] = preservation_types
            # because rgid depends on flowCellId and barcodeIndex, we will
            # spoof barcodeIndex so that pairing can work properly; see
            # build_sample in runner.operator.roslin_operator.bin
            metadata['R'] = get_r_orientation(pooled_normal.file_name)
            metadata['barcodeIndex'] = spoof_barcode(sample['file_name'], metadata['R'])
            metadata['flowCellId'] = 'PN_FCID'
            metadata['tumorOrNormal'] = 'Normal'
            metadata['patientId'] = 'PN_PATIENT_ID'
            sample['metadata'] = metadata
            sample_files.append(sample)
        pooled_normal = build_sample(sample_files, ignore_sample_formatting=True)
        return pooled_normal
    return None


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
