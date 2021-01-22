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


def get_request_id_runs(request_id):
    """
    Get the latest completed runs for the given request ID

    :param request_id: str - IGO request ID
    :return: List[str] - List of most recent runs from given request ID
    """
    group_id = Run.objects.filter(
        tags__requestId=request_id,
        app__name='access legacy',
        status=RunStatus.COMPLETED
    ).order_by('-finished_date').first().job_group

    request_id_runs = Run.objects.filter(
        job_group=group_id,
        status=RunStatus.COMPLETED
    )
    return request_id_runs


def get_unfiltered_matched_normal(patient_id):
    """
    Find a matched normal sample for the given patient ID with the following precedence:

    1. Latest Matched Normal from IGO ACCESS samples
    2. Latest Matched Normal from DMP ACCESS samples
    3. Return (None, ''), which will be used as a placeholder for skipping genotyping in the SNV pipeline

    Todo: generalize to work for duplex / simplex / standard, and use in MSI operator

    :return: (file_system.models.File - bam, str - sample_id)
    """
    patient_normals_search = patient_id + NORMAL_SAMPLE_SEARCH
    unfiltered_matched_normal_bam = File.objects.filter(file_name__startswith=patient_normals_search, file_name__endswith=IGO_UNFILTERED_REGEX)
    if len(unfiltered_matched_normal_bam) == 0:
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

        if len(unfiltered_matched_normal_bam) == 0:
            msg = 'WARNING: Could not find DMP or IGO matching unfiltered normal bam file for patient {}. ' \
                  'We will skip running this sample.'
            msg = msg.format(patient_id)
            logger.warning(msg)
            unfiltered_matched_normal_bam = None
            unfiltered_matched_normal_sample_id = ''
        else:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.order_by('-metadata__imported').first().file

    elif len(unfiltered_matched_normal_bam) > 1:
        msg = 'WARNING: Found more than one matching unfiltered normal bam file for patient {}. ' \
              'We will choose the most recently-created one for this run.'
        msg = msg.format(patient_id)
        logger.warning(msg)
        unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.order_by('-created_date').first()

    else:
        unfiltered_matched_normal_bam = unfiltered_matched_normal_bam[0]

    # Parse the Normal Sample ID from the file name
    # Todo: Stop using file path for this, once output_metadata is being supplied in access legacy operator
    if unfiltered_matched_normal_bam:
        unfiltered_matched_normal_file_base = unfiltered_matched_normal_bam.path.split('/')[-1]
        unfiltered_matched_normal_sample_id = '-'.join(unfiltered_matched_normal_file_base.split('-')[0:3])

    return unfiltered_matched_normal_bam, unfiltered_matched_normal_sample_id
