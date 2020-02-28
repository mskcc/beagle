from .make_sample import build_sample, remove_with_caveats
from file_system.models import File, FileMetadata
from django.db.models import Prefetch
from django.conf import settings
import logging
import os
from pathlib import Path
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
        logger.warning('Some samples for patient query %s have invalid %i values' % (patient_id, len(bad_samples)))
    return samples


# Need descriptor to match pooled normal "recipe", which might need to be re-labeled as bait_set
def get_descriptor(bait_set, pooled_normals):
    for f in pooled_normals:
        descriptor = f.filemetadata_set.first().metadata['recipe']
        if descriptor.lower() in bait_set.lower():
            return descriptor
    return None


def get_pooled_normals(run_id, preservation_type, bait_set):
    file_objs = File.objects.prefetch_related(Prefetch('filemetadata_set', queryset=FileMetadata.objects.select_related('file').order_by('-created_date'))) 
    pooled_normals = file_objs.filter(file_group=settings.POOLED_NORMAL_FILE_GROUP, filemetadata__metadata__runId=run_id, filemetadata__metadata__preservation=preservation_type).order_by('file_name')
    descriptor = get_descriptor(bait_set, pooled_normals)
    if not descriptor: # i.e., no pooled normal
        return None
    pooled_normals = pooled_normals.filter(filemetadata__metadata__recipe=descriptor)
    sample_files = list()
    sample_name = "pooled_normal_%s_%s_%s" % (descriptor, run_id, preservation_type)
    if len(pooled_normals) > 0:
        for i,f in enumerate(pooled_normals):
            sample = dict()
            sample['id'] = f.id
            sample['path'] = f.path
            sample['file_name'] = f.file_name
            print('i is %i: %s' %  (i, f.file_name))
            metadata = construct_fake_sample_fastq_metadata()
            metadata['sampleId'] = sample_name
            metadata['sampleName'] = sample_name
            metadata['requestId'] = sample_name
            metadata['baitSet'] = descriptor
            metadata['recipe'] = descriptor
            metadata['run_id'] = run_id
            metadata['preservation'] = preservation_type
            # because rgid depends on flowCellId and barcodeIndex, we will
            # spoof barcodeIndex so that pairing can work properly; see
            # build_sample in runner.operator.roslin_operator.bin
            metadata['R'] = get_r_orientation(f.file_name)
            metadata['barcodeIndex'] = spoof_barcode(sample['file_name'], metadata['R']) 
            metadata['flowCellId'] = 'PN_FCID'
            metadata['tumorOrNormal'] = 'Normal'
            metadata['patientId'] = 'PN_PATIENT_ID'
            sample['metadata'] = metadata
            sample_files.append(sample) 
        print("Number of samples: %i" % len(sample_files))
        pooled_normal = build_sample(sample_files, ignore_sample_formatting=True)
        return pooled_normal
    return None


def get_r_orientation(fastq_filename):
        reversed_str = ''.join(reversed(fastq_filename))
        if '1R' in reversed_str:
            return 'R1'
        if '2R' in reversed_str:
            return 'R2'
        return None


# Spoof barcode by removing 'R1' or 'R2' from the filename; paired fastqs
# are assumed to have only these two values as different
#
# We are also assuming there are no periods in the file names other than extensions
def spoof_barcode(sample_file_name, r_orientation):
    reversed_str = ''.join(reversed(sample_file_name))
    if r_orientation == 'R1':
        reversed_str = reversed_str.replace('1R', '')
    else:
        reversed_str = reversed_str.replace('2R', '')
    reversed_str = ''.join(reversed(reversed_str))
    spoofed_barcode = reversed_str.split(os.extsep)[0]
    return spoofed_barcode


def construct_fake_sample_fastq_metadata():
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
