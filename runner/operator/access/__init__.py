import logging

from runner.models import Run, RunStatus, Port
from file_system.models import File, FileMetadata


logger = logging.getLogger(__name__)

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam'
NORMAL_SAMPLE_SEARCH = '-N0'
DMP_UNFILTERED_REGEX = '-unfilter.bam'
IGO_UNFILTERED_REGEX = '__aln_srt_IR_FX.bam'
ACCESS_ASSAY = 'ACCESS_V1_0'
DMP_IMPACT_ASSAYS = ['IMPACT341', 'IMPACT410', 'IMPACT468', 'hemepact_v4']


def get_request_id(run_ids, request_id=None):
    if request_id:
        return request_id

    if run_ids:
        run = Run.objects.get(pk=run_ids[0])
        if run.tags.get('requestId'):
            return run.tags.get('requestId')

    raise Exception("Could not get find request id")

def get_request_id_runs(request_id):
    """
    Get the latest completed bam-generation runs for the given request ID

    :param request_id: str - IGO request ID
    :return: List[str] - List of most recent runs from given request ID
    """
    operator_run_id = Run.objects.filter(
        tags__requestId=request_id,
        app__name__in=['access legacy', 'access nucleo'],
        operator_run__status=RunStatus.COMPLETED
    ).exclude(finished_date__isnull=True).order_by('-finished_date').first().operator_run_id

    request_id_runs = Run.objects.filter(
        operator_run_id=operator_run_id,
        app__name__in=['access legacy', 'access nucleo'],
        status=RunStatus.COMPLETED
    )
    return request_id_runs


def extract_tumor_ports(ports):
    """
    Filter to just port objects from Tumor samples (or ports with anything *except* "N" in the timepoint

    Include: -T (Tumor), -P (primary), -M (metastatic), -L
    Exclude: -N (Normal)

    Todo: Use separate metadata fields for Tumor / sample ID designation instead of file name

    :param sample_ports:
    :return:
    """
    def is_tumor(port):
        file_name = port['location'].split('/')[-1]
        t_n_timepoint = file_name.split('-')[2]
        return not t_n_timepoint[0] == 'N'

    tumor_ports = [f for p in ports for f in p.value if is_tumor(f)]
    return tumor_ports


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
    unfiltered_matched_normal_sample_id = ''
    warnings = []

    # Case 1
    if request_id:
        # Todo: Joining to Port -> Run makes this query slow, make use of output_metadata for requestId instead
        unfiltered_matched_normal_bam = File.objects.filter(
            file_name__startswith=patient_normals_search,
            file_name__endswith=IGO_UNFILTERED_REGEX,
            port__run__tags__requestId__startswith=request_id.split('_')[0]
        ).order_by('-created_date').first()

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_sample_id = \
            unfiltered_matched_normal_bam.file_name.rstrip('_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam')

    # Case 2
    if not request_id or not unfiltered_matched_normal_bam:
        unfiltered_matched_normal_bam = File.objects.filter(
            file_name__startswith=patient_normals_search,
            file_name__endswith=IGO_UNFILTERED_REGEX
        ).order_by('-created_date').first()

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_sample_id = \
            unfiltered_matched_normal_bam.file_name.rstrip('_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam')

    # Case 3
    if not unfiltered_matched_normal_bam:
        warnings.append('WARNING: Could not find matching IGO unfiltered normal bam file for patient {}. '
              'Searching for DMP ACCESS sample.')

        unfiltered_matched_normal_bam = FileMetadata.objects.filter(
            metadata__cmo_assay=ACCESS_ASSAY,
            metadata__patient__cmo=patient_id.lstrip('C-'),
            metadata__type='N',
            file__path__endswith=DMP_UNFILTERED_REGEX
        ).order_by('-metadata__imported').first()

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.file
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip('.bam')

    # Case 4
    if not unfiltered_matched_normal_bam:
        warnings.append('WARNING: Could not find matching DMP ACCESS unfiltered normal bam file for patient {}. '
              'Searching for DMP IMPACT sample.')

        unfiltered_matched_normal_bam = FileMetadata.objects.filter(
            metadata__cmo_assay__in=DMP_IMPACT_ASSAYS,
            metadata__patient__cmo=patient_id.lstrip('C-'),
            metadata__type='N'
        ).order_by('-metadata__imported').first()

        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.file
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip('.bam')

    # Case 5
    if not unfiltered_matched_normal_bam:
        warnings.append('WARNING: Could not find DMP or IGO matching unfiltered normal bam file for patient {}. '
              'We will skip matched normal genotyping for this sample.')

        unfiltered_matched_normal_bam = None
        unfiltered_matched_normal_sample_id = ''

    for msg in warnings:
        msg = msg.format(patient_id)
        logger.warning(msg)

    return unfiltered_matched_normal_bam, unfiltered_matched_normal_sample_id


def get_most_recent_files_for_request(app, request_id, name=None):
    """
    Given a request ID, return File objects associated with Ports from the most recent run of the given `app`

    :param app: str - name of pipeline to get outputs from
    :param request_id: str - IGO request id
    :param name: str - optional name of port to be queried
    :return: str[] - file paths for outputs of most recent run
    """
    most_recent_run = Run.objects.filter(app=app, tags__requestId=request_id).order_by('-created_date').first()

    # Get all standard bam ports for these runs
    port = Port.objects.filter(
        name=name,
        run__id=most_recent_run.pk,
        run__status=RunStatus.COMPLETED
    )

    return [f.path for f in port.files]
