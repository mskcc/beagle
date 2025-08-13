import logging

from django.conf import settings
from runner.models import Run, RunStatus, Port
from file_system.models import File, FileMetadata

logger = logging.getLogger(__name__)

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = "access_curated_normals"
ACCESS_DEFAULT_NORMAL_ID = "DONOR22-TP"
ACCESS_DEFAULT_NORMAL_FILENAME = "DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
NORMAL_SAMPLE_SEARCH = "-N0"
DMP_UNFILTERED_REGEX = "-unfilter.bam"
IGO_UNFILTERED_REGEX = "__aln_srt_IR_FX.bam"
ACCESS_ASSAY = "ACCESS_V1_0"
DMP_IMPACT_ASSAYS = ["IMPACT341", "IMPACT410", "IMPACT468", "hemepact_v4"]


def get_request_id(run_ids, request_id=None):
    if request_id:
        return request_id

    if run_ids:
        run = Run.objects.get(pk=run_ids[0])
        if run.tags.get(settings.REQUEST_ID_METADATA_KEY):
            return run.tags.get(settings.REQUEST_ID_METADATA_KEY)

    raise Exception("Could not get find request id")


def get_request_id_runs(app, run_ids, request_id):
    """
    Get the latest completed bam-generation runs for the given request ID

    :param request_id: str - IGO request ID
    :return: List[str] - List of most recent runs from given request ID
    """

    if run_ids:
        most_recent_runs_for_request = Run.objects.filter(pk__in=run_ids, status=RunStatus.COMPLETED)
        request_id = most_recent_runs_for_request[0].tags[settings.REQUEST_ID_METADATA_KEY]
    elif request_id:
        most_recent_runs_for_request = (
            Run.objects.filter(
                tags__igoRequestId=request_id,
                app__name__in=app,
                status=RunStatus.COMPLETED,
                operator_run__status=RunStatus.COMPLETED,
            )
            .order_by("-created_date")
            .first()
            .operator_run.runs.all()
            .filter(status=RunStatus.COMPLETED)
        )
        if not len(most_recent_runs_for_request):
            raise Exception(f"No matching {app} runs found for request {request_id}")
    else:
        raise Exception(f"No valid run or request id for {app}")
    return most_recent_runs_for_request, request_id


def create_cwl_file_object(file_path, url="juno://"):
    """
    Util function to create a simple CWL File object from a file_path

    :param file_path: str
    :return:
    """
    return {"class": "File", "location": url + file_path}


def is_tumor(file):
    file_name = file["location"].split("/")[-1]
    t_n_timepoint = file_name.split("-")[2]
    return not t_n_timepoint[0] == "N"


def get_unfiltered_matched_normal(patient_id, request_id=None):
    """
    Find a matched normal sample for the given patient ID with the following precedence:

    1. Latest Matched Normal from IGO ACCESS samples (same request)
    2. Latest Matched Normal from IGO ACCESS samples (any request)
    3. Latest Matched Normal from DMP ACCESS samples
    4. Latest Matched Normal from DMP IMPACT samples
    5. Return (None, ''), which will be used as a placeholder for skipping genotyping in the SNV pipeline

    Todo: generalize to work for duplex / simplex / standard, and use in MSI operator

    :param: patient_id - str Patient ID in CMO format (C-ABC123)
    :param: request_id - str IGO request ID (06302_AA)
    :return: (file_system.models.File - bam, str - sample_id)
    """
    patient_normals_search = patient_id + NORMAL_SAMPLE_SEARCH
    unfiltered_matched_normal_bam = None
    unfiltered_matched_normal_sample_id = ""
    warnings = []

    # Case 1
    if request_id:
        # Todo: Joining to Port -> Run makes this query slow, make use of output_metadata for requestId instead
        unfiltered_matched_normal_bam = (
            File.objects.filter(
                file_name__startswith=patient_normals_search,
                file_name__endswith=IGO_UNFILTERED_REGEX,
                port__run__tags__igoRequestId__startswith=request_id.split("_")[0],
            )
            .order_by("-created_date")
            .first()
        )

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(
                "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam"
            )

    # Case 2
    if not request_id or not unfiltered_matched_normal_bam:
        unfiltered_matched_normal_bam = (
            File.objects.filter(file_name__startswith=patient_normals_search, file_name__endswith=IGO_UNFILTERED_REGEX)
            .order_by("-created_date")
            .first()
        )

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(
                "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam"
            )

    # Case 3
    if not unfiltered_matched_normal_bam:
        warnings.append(
            "WARNING: Could not find matching IGO unfiltered normal bam file for patient {}. "
            "Searching for DMP ACCESS sample."
        )

        unfiltered_matched_normal_bam = (
            FileMetadata.objects.filter(
                metadata__cmo_assay=ACCESS_ASSAY,
                metadata__patient__cmo=patient_id.lstrip("C-"),
                metadata__type="N",
                file__path__endswith=DMP_UNFILTERED_REGEX,
            )
            .order_by("-metadata__imported")
            .first()
        )

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.file
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(".bam")

    # Case 4
    if not unfiltered_matched_normal_bam:
        warnings.append(
            "WARNING: Could not find matching DMP ACCESS unfiltered normal bam file for patient {}. "
            "Searching for DMP IMPACT sample."
        )

        unfiltered_matched_normal_bam = (
            FileMetadata.objects.filter(
                metadata__cmo_assay__in=DMP_IMPACT_ASSAYS,
                metadata__patient__cmo=patient_id.lstrip("C-"),
                metadata__type="N",
            )
            .order_by("-metadata__imported")
            .first()
        )

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.file
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(".bam")

    # Case 5
    if not unfiltered_matched_normal_bam:
        warnings.append(
            "WARNING: Could not find DMP or IGO matching unfiltered normal bam file for patient {}. "
            "We will skip matched normal genotyping for this sample."
        )

        unfiltered_matched_normal_bam = None
        unfiltered_matched_normal_sample_id = ""

    for msg in warnings:
        msg = msg.format(patient_id)
        logger.warning(msg)

    return unfiltered_matched_normal_bam, unfiltered_matched_normal_sample_id


def parse_nucleo_output_ports(run, port_name):
    bam_bai = Port.objects.get(name=port_name, run=run.pk)
    if not len(bam_bai.files.all()) in [1, 2]:
        raise Exception("Port {} for run {} should have just 1 bam or 1 (bam/bai) pair".format(port_name, run.id))
    bam = [b for b in bam_bai.files.all() if b.file_name.endswith(".bam")][0]
    return bam


def find_request_bams(run):
    """
    Find simplex and duplex bams from a request's nucleo run
    - run_ids: run_ids from a request's nucleo run

    :return: list of paired simplex and duplex bams and normal bam
    """
    nucleo_output_port_names = [
        "uncollapsed_bam",
        "fgbio_group_reads_by_umi_bam",
        "fgbio_collapsed_bam",
        "fgbio_filter_consensus_reads_duplex_bam",
        "fgbio_postprocessing_simplex_bam",
    ]
    bams = {}
    for o in nucleo_output_port_names:
        # We are running a multi-sample workflow on just one sample,
        # so we create single-element lists here
        bam = parse_nucleo_output_ports(run, o)
        bams[o] = bam

    return bams


def is_tumor_bam(file):
    if not file.endswith(".bam"):
        return False
    t_n_timepoint = file.split("-")[2]
    return not t_n_timepoint[0] == "N"



