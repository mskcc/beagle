import os
from datetime import datetime as dt

from django.conf import settings
from django.db.models import Q

from file_system.repository.file_repository import FileRepository

from ..bin.pair_object import PairObj
from ..bin.pairs_object import PairsObj
from ..bin.patient_object import PatientObj
from ..bin.sample_dmp import SampleDMP, SampleDMPManager
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
    From metadata, find SampleDMPs through SampleDMPManager

    Returns dmp_samples, which can get dmp normal through

        dmp_samples.dmp_normal

    and all samples through

        dmp_samples.all_dmp_bams
    """
    dmp_samples = SampleDMPManager(metadata)

    return dmp_samples


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
        request_id_sample = metadata[settings.REQUEST_ID_METADATA_KEY]
        sample_type = sample.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
        run_mode = get_run_mode(sample.run_mode)
        bait_set = sample.metadata[settings.BAITSET_METADATA_KEY]
        files = FileRepository.all()
        samples = get_samples_igo(patient_id, files)
        samples_normals_igo = [
            samples[s]
            for s in samples
            if "normal" in (samples[s].metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY].lower() or "")
            and samples[s].metadata[settings.BAITSET_METADATA_KEY].lower() in bait_set.lower()
        ]
        pooled_normals = [get_samples_pooled_normals(metadata)]
        dmp_bams = get_samples_dmp(metadata)

        # Creating a full list of all normals that can be connected to every tumor
        for dmp_sample in dmp_bams.all_dmp_bams:
            if "normal" in dmp_sample.metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY].lower():
                normal = dmp_sample
                pair = PairObj(sample, normal)
                pairs_full.add_pair(pair)

        for normal in pooled_normals:
            pair = PairObj(sample, normal)
            best_normal = normal  # assigning default "best" normal, which is the pooled normal; overwritten if better match exists
            pairs_full.add_pair(pair)

        for normal in samples_normals_igo:
            pair = PairObj(sample, normal)
            pairs_full.add_pair(pair)

        # retrieve "best" pair, based on WITHIN Request; OUTSIDE request; or POOLED pooled_normals
        # filter for normals in request
        samples_normals_igo_same_request = [
            s for s in samples_normals_igo if s.metadata[settings.REQUEST_ID_METADATA_KEY] == request_id_sample
        ]
        best_normal_igo = get_viable_normal(samples_normals_igo_same_request, run_mode, request_id_sample)
        if best_normal_igo:
            best_normal = best_normal_igo
        elif dmp_bams.dmp_bam_normal:
            best_normal = dmp_bams.dmp_bam_normal

        if best_normal:
            pairs_best.add_pair(PairObj(best_normal, sample))
        else:
            print("No normal found")

    return pairs_best, pairs_full


def pair_patient_samples(patient):
    pass


def compare_dates(normal, viable_normal, date_string):
    """
    Compares dates between two normals; returns the most recent
    """
    for run_date in normal["run_date"]:
        normal_date = dt.strptime(run_date, date_string)
        for vrun_date in viable_normal["run_date"]:
            vnormal_date = dt.strptime(vrun_date, date_string)
            if vnormal_date < normal_date:
                viable_normal = normal


def get_viable_normal(normals, run_mode, request_id_sample=None):
    """
    From a set of normals, return the ones that have run_mode and the most recent

    Does not check for Pooled Normals; that's done separately
    """
    viable_normal = dict()
    for normal in normals:
        normal_run_mode = get_run_mode(normal.run_mode)
        if normal_run_mode == run_mode:
            if viable_normal:
                try:
                    viable_normal = compare_dates(normal, viable_normal, "%y-%m-%d")
                except ValueError:
                    viable_normal = compare_dates(normal, viable_normal, "%Y-%m-%d")
            else:
                viable_normal = normal
    return viable_normal


def get_run_mode(run_mode):
    """
    Normalizing hiseq and novaseq strings
    """
    if run_mode:
        if "hiseq" in run_mode.lower():
            return "hiseq"
        if "novaseq" in run_mode.lower():
            return "novaseq"
    return run_mode
