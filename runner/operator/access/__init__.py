import logging

from runner.models import Run, RunStatus
from file_system.models import File, FileMetadata


logger = logging.getLogger(__name__)

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam'
NORMAL_SAMPLE_SEARCH = '-N0'
DMP_UNFILTERED_REGEX = '-unfilter.bam'
IGO_UNFILTERED_REGEX = '__aln_srt_IR_FX.bam'


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
    Get the latest completed runs for the given request ID

    :param request_id: str - IGO request ID
    :return: List[str] - List of most recent runs from given request ID
    """
    operator_run_id = Run.objects.filter(
        tags__requestId=request_id,
        app__name='access legacy',
        operator_run__status=RunStatus.COMPLETED
    ).exclude(finished_date__isnull=True).order_by('-finished_date').first().operator_run_id

    request_id_runs = Run.objects.filter(
        operator_run_id=operator_run_id,
        app__name='access legacy',
        status=RunStatus.COMPLETED
    )
    return request_id_runs


def get_unfiltered_matched_normal(patient_id, request_id=None):
    """
    Find a matched normal sample for the given patient ID with the following precedence:

    1. Latest Matched Normal from IGO ACCESS samples (same request)
    2. Latest Matched Normal from IGO ACCESS samples (any request)
    3. Latest Matched Normal from DMP ACCESS samples
    4. Return (None, ''), which will be used as a placeholder for skipping genotyping in the SNV pipeline

    Todo: generalize to work for duplex / simplex / standard, and use in MSI operator

    :param: patient_id - str Patient ID in CMO format (C-ABC123)
    :param: request_id - str IGO request ID (06302_AA)
    :return: (file_system.models.File - bam, str - sample_id)
    """
    patient_normals_search = patient_id + NORMAL_SAMPLE_SEARCH
    unfiltered_matched_normal_bam = None

    # Case 1
    if request_id:
        unfiltered_matched_normal_bam = File.objects.filter(
            file_name__startswith=patient_normals_search,
            file_name__endswith=IGO_UNFILTERED_REGEX,
            port__run__tags__request_id__startswith=request_id.split('_')[0]
        )
    # Case 2
    if not request_id or len(unfiltered_matched_normal_bam) == 0:
        unfiltered_matched_normal_bam = File.objects.filter(
            file_name__startswith=patient_normals_search,
            file_name__endswith=IGO_UNFILTERED_REGEX
        )

    if len(unfiltered_matched_normal_bam) > 1:
        msg = 'WARNING: Found more than one matching unfiltered normal bam file for patient {}. ' \
              'We will choose the most recently-created one for this run.'
        msg = msg.format(patient_id)
        logger.warning(msg)
        unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.order_by('-created_date').first()

    elif len(unfiltered_matched_normal_bam) == 1:
        unfiltered_matched_normal_bam = unfiltered_matched_normal_bam[0]

    # Case 3
    elif len(unfiltered_matched_normal_bam) == 0:
        msg = 'WARNING: Could not find IGO matching unfiltered normal bam file for patient {}. ' \
              'Searching for DMP sample.'
        msg = msg.format(patient_id)
        logger.warning(msg)

        unfiltered_matched_normal_bam = FileMetadata.objects.filter(
            metadata__cmo_assay='ACCESS_V1_0',
            metadata__patient__cmo=patient_id.replace('C-', ''),
            metadata__type='N',
            file__path__endswith=DMP_UNFILTERED_REGEX
        )

        # Case 4
        if len(unfiltered_matched_normal_bam) == 0:
            msg = 'WARNING: Could not find DMP or IGO matching unfiltered normal bam file for patient {}. ' \
                  'We will skip matched normal genotyping for this sample.'
            msg = msg.format(patient_id)
            logger.warning(msg)

            unfiltered_matched_normal_bam = None
            unfiltered_matched_normal_sample_id = ''
        else:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.order_by('-metadata__imported').first().file

    # Parse the Normal Sample ID from the file name
    # Todo: Use output_metadata on Bams instead
    if unfiltered_matched_normal_bam:
        unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.split('_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam')[0]

    return unfiltered_matched_normal_bam, unfiltered_matched_normal_sample_id
