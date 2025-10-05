import os

from django.conf import settings
from django.db.models import Q

from file_system.repository.file_repository import FileRepository

from ..bin.pair_object import PairObj
from ..bin.pairs_object import PairsObj
from ..bin.patient_object import PatientObj
from ..bin.sample_dmp import SampleDMP
from ..bin.sample_igo import SampleIGO
from ..bin.sample_pooled_normal import SamplePooledNormal


def get_samples_igo(patient_id, files_set):
    files = FileRepository.filter(
        queryset=files_set,
        metadata={settings.PATIENT_ID_METADATA_KEY: patient_id},
    )

    file_list = dict()
    samples = dict()

    for f in files:
        sample_name = f.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
        if sample_name not in file_list:
            file_list[sample_name] = list()
        file_list[sample_name].append(f)

    for sample_name in file_list:
        sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")
        samples[sample_name] = sample_igo

    return samples


def get_samples_dmp(metadata):
    """
    From metadata, find SampleDMPs
    """
    sample_dmp = SampleDMP(metadata)
    return sample_dmp


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


def pair_samples_igo(samples_tumor, request_id=None):
    """
    Get all viable normal pairings for these samples

    Return two things: the "best" pairing and the "verbose" pairings per sample
    """

    from pprint import pprint

    pairs_best = PairsObj()
    pairs_full = PairsObj()
    for sample in samples_tumor:
        metadata = sample.metadata
        patient_id = metadata[settings.PATIENT_ID_METADATA_KEY]
        request_id_in_sample = metadata[settings.REQUEST_ID_METADATA_KEY]
        sample_type = sample.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
        files = FileRepository.all()
        samples = get_samples_igo(patient_id, files)
        print(metadata["ciTag"], sample_type)
        pprint(samples)
        samples_normals_igo = [
            samples[s]
            for s in samples
            if "normal" in (samples[s].metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY].lower() or "")
        ]
        pooled_normals = [get_samples_pooled_normals(metadata)]
        dmp_normal = get_samples_dmp(metadata)

        # Creating a full list of all normals that can be connected to every tumor
        for normal in dmp_normal.all_dmp_bams:
            pair = PairObj(sample, normal)
            pairs_full.add_pair(pair)

        for normal in samples_normals_igo:
            pprint(normal)
            pair = PairObj(sample, normal)
            pairs_full.add_pair(pair)

        for normal in pooled_normals:
            pair = PairObj(sample, normal)
            pairs_full.add_pair(pair)

        # retrieve "best" pair, based on WITHIN Request; OUTSIDE request; or POOLED NORMAL
    return pairs_best, pairs_full


def pair_patient_samples(patient):
    pass
