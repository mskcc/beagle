"""
Functions for retrieving samples from the database based on other criteria
that wasn't in the operator

For example, get all samples by a patient ID or pooled normals based on the bait set
and preservation type
"""

import logging
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from file_system.models import File, FileGroup, MachineRunMode, PooledNormal
from file_system.repository.file_repository import FileRepository
from runner.operator.helper import get_r_orientation, init_metadata, spoof_barcode

from .make_sample import build_sample, format_sample_name, remove_with_caveats

LOGGER = logging.getLogger(__name__)


def build_argos_file_groups_query():
    ARGOS_FG_SLUGS = ["lims", "origin-unknown"]
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
    q_pid = Q(("metadata__{}".format(settings.PATIENT_ID_METADATA_KEY), patient_id))
    q_fg = build_argos_file_groups_query()
    q = q_pid & q_fg
    files = FileRepository.filter(queryset=all_files, q=q)
    files = FileRepository.filter(queryset=files, filter_redact=True)
    data = list()
    for current_file in files:
        sample = dict()
        sample["id"] = current_file.file.id
        sample["path"] = current_file.file.path
        sample["file_name"] = current_file.file.file_name
        sample["metadata"] = current_file.metadata
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
    number_of_bad_samples = len(bad_samples)
    if number_of_bad_samples > 0:
        LOGGER.warning("Some samples for patient query %s have invalid %i values", patient_id, number_of_bad_samples)
    return samples


def get_descriptor(bait_set, pooled_normals, preservation_types, run_ids, sample_origin):
    """
    Need descriptor to match pooled normal bait_set (legacy)

    OR

    Retrieve a static pooled normal from file_system_poolednormal table (novaseq X change)
    """
    query = Q(file__file_group=settings.POOLED_NORMAL_FILE_GROUP)
    sample_name = None

    descriptor = None
    for pooled_normal in pooled_normals:
        bset_data = pooled_normal.metadata[settings.RECIPE_METADATA_KEY]
        if bset_data.lower() in bait_set.lower():
            descriptor = bset_data

    # From returned pooled normals, we found the bait set/genePanel we're looking for
    # This is for legacy pooled normals (i.e., IMPACT341, IMPACT410, IMPACT468)
    if descriptor:
        pooled_normals = FileRepository.filter(
            queryset=pooled_normals, metadata={settings.RECIPE_METADATA_KEY: descriptor}
        )

        # sample_name is FROZENPOOLEDNORMAL unless FFPE is in any of the preservation types
        # in preservation_types; plc = preservations lower case
        plc = set([x.lower() for x in preservation_types])
        run_ids_suffix_list = [i for i in run_ids if i]  # remove empty or false string values
        run_ids_suffix = "_".join(set(run_ids_suffix_list))
        sample_name = "FROZENPOOLEDNORMAL_" + run_ids_suffix
        if "ffpe" in plc:
            sample_name = "FFPEPOOLEDNORMAL_" + run_ids_suffix
    else:
        earliest_pooled_normal = None
        machines = get_machines_by_substr(run_ids)
        baits = bait_set.lower()
        # plc = preservation lower case; slc = sample origin lower case
        preservation = get_preservation_type(preservation_types, sample_origin)

        for machine in machines:
            pooled_normal_objs = PooledNormal.objects.filter(
                machine=machine, preservation_type=preservation, bait_set=baits
            )
            if not pooled_normal_objs:
                continue
            if not earliest_pooled_normal:
                earliest_pooled_normal = pooled_normal_objs.first()
            else:
                pooled_normal = pooled_normal_objs.first()
                if not earliest_pooled_normal:
                    earliest_pooled_normal = pooled_normal
                else:
                    # tiebreaker - if there's more than one set of pooled normals fetched, return earliest one
                    old_date = earliest_pooled_normal.run_date
                    curr_date = pooled_normal.run_date
                    if curr_date < old_date:
                        earliest_pooled_normal = pooled_normal

        if earliest_pooled_normal:
            sample_name = "_".join(
                [
                    earliest_pooled_normal.bait_set,
                    earliest_pooled_normal.preservation_type,
                    earliest_pooled_normal.machine,
                    "POOLEDNORMAL",
                ]
            )
            sample_name = sample_name.upper()
            descriptor = baits
            all_files = FileRepository.filter(file_group=settings.POOLED_NORMAL_FILE_GROUP)
            pooled_normals = list()
            for pn in earliest_pooled_normal.pooled_normals_paths:
                pn_file = FileRepository.filter(queryset=all_files, path=pn).first()
                pooled_normals.append(pn_file)

    return pooled_normals, descriptor, sample_name


def get_preservation_type(preservation_types, sample_origin):
    """
    From preservation type and sample origin list:
        - convert them to lower case lists plc and solc
        - if both have values, check that they are the same, ie
            - if sample origin is "fresh or frozen", make sure preservation is NOT ffpe
            - if preservation is FFPE, make sure sample origin is also FFPE
        - if preservation_type is empty, check sample origin, where:
            - sample origin is either 'ffpe' is 'fresh or frozen' (which equals 'frozen')
        - if preservation_type is not empty:
            - return 'ffpe' if is_ffpe(); otherwise 'frozen'
    """
    plc = set([x.lower() for x in preservation_types])  # preservation lower case
    solc = set([x.lower() for x in sample_origin])  # sample origin lower case
    preservation = ""

    if not is_list_empty(plc) and not is_list_empty(solc):
        if is_ffpe(plc) and is_ffpe(solc):
            preservation = "ffpe"
        else:
            if "fresh or frozen" in solc:
                if not is_ffpe(plc):
                    preservation = "frozen"
    elif not is_list_empty(plc):
        print(f"Assigning preservation type by plc: {plc}")
        if is_ffpe(plc):
            preservation = "ffpe"
        else:
            preservation = "frozen"
    elif not is_list_empty(solc):
        print(f"Doing sample origin resolution for solc: {solc}")
        if is_ffpe(solc):
            preservation = "ffpe"
        if "fresh or frozen" in solc:
            preservation = "frozen"
    return preservation


def is_ffpe(l):
    """
    In list l, if any item is 'ffpe', consider sample as FFPE and return True
    """
    if "ffpe" in l:
        return True


def get_sequencer_type(run_ids_list):
    run_ids_lower = [i.lower() for i in run_ids_list if i]
    machine_modes = MachineRunMode.objects.all()
    for machine in machine_modes:
        if find_substr(machine.machine_name, run_ids_lower):
            return machine.machine_class


# Unfortunately, we need to get machine name from runId
# runIds are expected to be delimited by "_"; machine is the 0th element on split
def get_machines_by_substr(run_ids):
    machines = [i.split("_")[0].lower() for i in run_ids]
    return machines


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
    plc = set([x.lower() for x in data])
    value = "FROZEN"
    if "ffpe" in plc:
        value = "FFPE"
    # case-insensitive matching
    query = Q(metadata__preservation__iexact=value)
    return query


def get_pooled_normals(run_ids, preservation_types, bait_set, sample_origin):
    """
    From a list of run_ids, preservation types, and bait sets, get all potential pooled normals
    """
    pooled_normals, descriptor, sample_name = get_pooled_normal_files(
        run_ids, preservation_types, bait_set, sample_origin
    )
    sample_files = list()
    for pooled_normal_file in pooled_normals:
        sample_file = build_pooled_normal_sample_by_file(
            pooled_normal_file, run_ids, preservation_types, descriptor, sample_origin, sample_name
        )
        sample_files.append(sample_file)
    pooled_normal = build_sample(sample_files, ignore_sample_formatting=True)
    if not sample_files:
        return None
    return pooled_normal


def get_pooled_normal_files(run_ids, preservation_types, bait_set, sample_origin):

    pooled_normals = FileRepository.filter(file_group=settings.POOLED_NORMAL_FILE_GROUP)

    query = Q(file__file_group=settings.POOLED_NORMAL_FILE_GROUP)
    run_id_query = build_run_id_query(run_ids)
    preservation_query = build_preservation_query(preservation_types)

    q = query & run_id_query & preservation_query

    pooled_normals = FileRepository.filter(queryset=pooled_normals, q=q)

    pooled_normals, descriptor, sample_name = get_descriptor(
        bait_set, pooled_normals, preservation_types, run_ids, sample_origin
    )

    return pooled_normals, descriptor, sample_name


def build_pooled_normal_sample_by_file(
    pooled_normal, run_ids, preservation_types, bait_set, sample_origin, sample_name
):
    specimen_type = "Pooled Normal"
    sample = dict()
    sample["id"] = pooled_normal.file.id
    sample["path"] = pooled_normal.file.path
    sample["file_name"] = pooled_normal.file.file_name
    metadata = init_metadata()
    metadata[settings.SAMPLE_ID_METADATA_KEY] = sample_name
    metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = sample_name
    metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = sample_name
    metadata[settings.REQUEST_ID_METADATA_KEY] = sample_name
    metadata["sequencingCenter"] = "MSKCC"
    metadata["platform"] = "Illumina"
    metadata["baitSet"] = bait_set
    metadata[settings.RECIPE_METADATA_KEY] = bait_set
    metadata["sampleOrigin"] = sample_origin
    metadata["runId"] = run_ids
    metadata["preservation"] = preservation_types
    metadata[settings.LIBRARY_ID_METADATA_KEY] = sample_name + "_1"
    # because rgid depends on flowCellId and barcodeIndex, we will
    # spoof barcodeIndex so that pairing can work properly; see
    # build_sample in runner.operator.argos_operator.bin
    metadata["R"] = get_r_orientation(pooled_normal.file.file_name)
    metadata["barcodeIndex"] = spoof_barcode(sample["file_name"], metadata["R"])
    metadata["flowCellId"] = "PN_FCID"
    metadata["tumorOrNormal"] = "Normal"
    metadata[settings.PATIENT_ID_METADATA_KEY] = "PN_PATIENT_ID"
    metadata[settings.SAMPLE_CLASS_METADATA_KEY] = specimen_type
    metadata["runMode"] = ""
    metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = ""
    sample["metadata"] = metadata
    return sample


def get_dmp_bam(patient_id, bait_set, tumor_type):
    """
    From a patient id and bait set, get matching dmp bam normal
    """
    file_objs = FileRepository.all()

    dmp_query = build_dmp_query(patient_id, bait_set)

    dmp_bam = FileRepository.filter(queryset=file_objs, q=dmp_query).order_by("file__file_name").first()

    if dmp_bam:
        sample = build_dmp_sample(dmp_bam, patient_id, bait_set, tumor_type)
        built_sample = build_sample([sample], ignore_sample_formatting=True)
        return built_sample
    return None


def build_dmp_sample(dmp_bam, patient_id, bait_set, tumor_type, request_id=None, pi=None, pi_email=None):

    dmp_metadata = dmp_bam.metadata
    specimen_type = "DMP"
    sample_name = dmp_metadata["external_id"]
    sequencingCenter = "MSKCC"
    platform = "Illumina"
    sample = dict()
    sample["id"] = dmp_bam.file.id
    sample["path"] = dmp_bam.file.path
    sample["file_name"] = dmp_bam.file.file_name
    sample["file_type"] = dmp_bam.file.file_type
    metadata = init_metadata()
    metadata[settings.SAMPLE_ID_METADATA_KEY] = format_sample_name(sample_name, specimen_type)
    metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = format_sample_name(sample_name, specimen_type)
    metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY]
    metadata[settings.REQUEST_ID_METADATA_KEY] = request_id
    metadata["request_id"] = request_id
    metadata["investigatorSampleId"] = dmp_metadata["sample"]
    metadata["sequencingCenter"] = sequencingCenter
    metadata["platform"] = platform
    metadata["baitSet"] = bait_set
    metadata[settings.RECIPE_METADATA_KEY] = bait_set
    metadata["run_id"] = ""
    metadata["preservation"] = ""
    metadata[settings.LIBRARY_ID_METADATA_KEY] = sample_name + "_1"
    metadata["R"] = "Not applicable"
    # because rgid depends on flowCellId and barcodeIndex, we will
    # spoof barcodeIndex so that pairing can work properly; see
    # build_sample in runner.operator.argos_operator.bin
    metadata["barcodeIndex"] = "DMP_BARCODEIDX"
    metadata["flowCellId"] = "DMP_FCID"
    metadata["tumorOrNormal"] = tumor_type
    metadata["sampleType"] = tumor_type
    metadata[settings.PATIENT_ID_METADATA_KEY] = patient_id
    metadata[settings.SAMPLE_CLASS_METADATA_KEY] = specimen_type
    metadata["runMode"] = ""
    metadata["sex"] = ""
    metadata["tissueLocation"] = dmp_metadata.get("tissue_type", "")
    metadata[settings.ONCOTREE_METADATA_KEY] = dmp_metadata.get("tumor_type", "")
    metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = ""
    if pi:
        metadata["pi"] = pi
    if pi_email:
        metadata["pi_email"] = pi_email
    sample["metadata"] = metadata
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
    normal = Q(metadata__type="N")
    query = assay & patient & normal
    return query


def is_list_empty(lst):
    return all(not bool(item) for item in lst)
