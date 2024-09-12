import copy
import os
import csv
import logging
from django.db.models import Q
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.models import Pipeline
import runner.operator.chronos_operator.bin.tempo_patient as patient_obj
from notifier.models import JobGroup
from notifier.events import OperatorRequestEvent, ChronosMissingSamplesEvent
from notifier.tasks import send_notification
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File
from runner.models import Port, RunStatus
from file_system.models import FileMetadata
from runner.models import RunStatus, Port, Run
import json 

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)
ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = "access_curated_normals"
ACCESS_DEFAULT_NORMAL_ID = "DONOR22-TP"
ACCESS_DEFAULT_NORMAL_FILENAME = "DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
NORMAL_SAMPLE_SEARCH = "-N0"
TUMOR_SAMPLE_SEARCH = "-L0"
DUPLEX_BAM_SEARCH = "__aln_srt_IR_FX-duplex.bam"
SIMPLEX_BAM_SEARCH = "__aln_srt_IR_FX-simplex.bam"
UNFILTERED_BAM_SEARCH = "__aln_srt_IR_FX.bam"
DMP_DUPLEX_REGEX = "-duplex.bam"
DMP_SIMPLEX_REGEX = "-simplex.bam"
DMP_UNFILTERED_REGEX = "-unfilter.bam"
DMP_REGEX = "-standard.bam"
IGO_UNFILTERED_REGEX = "__aln_srt_IR_FX.bam" 
ACCESS_ASSAY_HC = "HC_ACCESS"
DMP_IMPACT_ASSAYS = ["IMPACT341", "IMPACT410", "IMPACT468", "hemepact_v4"]
DMP_FILE_GROUP = "d4775633-f53f-412f-afa5-46e9a86b654b"
DUPLEX_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
SIMPLEX_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-simplex.bam"
UNCOLLAPSED_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR"



def _create_cwl_bam_object(bam):
    """
    Util function to create a simple CWL File object from a bam with a path attribute

    :param bam:
    :return:
    """
    return {"class": "File", "location": "juno://" + bam}


def _remove_normal_dups(
    geno_samples_normal_unfiltered,
    geno_samples_normal_unfiltered_sample_ids,
    capture_samples_duplex_sample_ids,
):
    """
    Make sure none of the normals are already present in duplex genotyping samples (GBCMS can not have
    duplicate sample IDs)

    :param geno_samples_normal_unfiltered:
    :param geno_samples_normal_unfiltered_sample_ids:
    :param capture_samples_duplex_sample_ids:
    :return:
    """
    deduped = []
    deduped_ids = []
    for i, s in enumerate(geno_samples_normal_unfiltered_sample_ids):
        if not any([sid in s for sid in capture_samples_duplex_sample_ids]):
            deduped_ids.append(s)
            deduped.append(geno_samples_normal_unfiltered[i])
    return deduped, deduped_ids


def split_duplex_simplex(files):
    '''
    given a list split file paths using -simplex and -duplex root
    :param files: a list of simplex/duplex file path 
    :return: two lists of file paths: one for simplex, one for duplex
    '''
    simplex = [] 
    duplex = [] 
    for f in files:
        if f.file_name.endswith('-simplex.bam'):
            simplex.append(f)
        if f.file_name.endswith('-duplex.bam'):
            duplex.append(f)
        else:
            ValueError('Expecting a list of duplex and simplex bams')  
    return duplex, simplex

def make_pairs(d, s):
    paired = []
    for di in d:
        for si in s:
            if di.file_name.rstrip("-duplex.bam") == si.file_name.rstrip("-simplex.bam"):
                paired.append((di, si))
    return paired


def parse_nucleo_output_ports(run, port_name):
    bam_bai = Port.objects.get(name=port_name, run=run.pk)
    if not len(bam_bai.files.all()) in [1, 2]:
        raise Exception("Port {} for run {} should have just 1 bam or 1 (bam/bai) pair".format(port_name, run.id))
    bam = [b for b in bam_bai.files.all() if b.file_name.endswith(".bam")][0]
    return bam

def is_tumor_bam(file):
    if not file.endswith(".bam"):
        return False
    t_n_timepoint = file.split("-")[2]
    return not t_n_timepoint[0] == "N"


def get_unfiltered_matched_normal(patient_id, fillout_unfiltered_normals, request_id=None):
    """
    Find a matched normal sample for the given patient ID with the following precedence:
    1. Latest Matched Normal from IGO ACCESS samples (same request)
    2. Latest Matched Normal from IGO ACCESS samples (study level 06302_*)
    3. Latest Matched Normal from IGO ACCESS samples (any request)
    4. Latest Matched Normal from DMP ACCESS samples 
    5. Latest Matched Normal from DMP IMPACT samples
    6. Return (None, ''), which will be used as a placeholder for skipping genotyping in the SNV pipeline

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
        for bam in fillout_unfiltered_normals:
            if bam.file_name.startswith(patient_normals_search):
                unfiltered_matched_normal_bam = bam
        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.replace(UNCOLLAPSED_BAM_STEM, "")
    # Case 2
    if not request_id or not unfiltered_matched_normal_bam:
        unfiltered_matched_normal_bam = (
            File.objects.filter(file_name__startswith=patient_normals_search, 
                                file_name__endswith=IGO_UNFILTERED_REGEX,
                                port__run__tags__igoRequestId__startswith=request_id.split("_")[0]
                                )
            .order_by("-created_date")
            .first()
        )
        
        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(".bam")
    # Case 3
    if not request_id or not unfiltered_matched_normal_bam:
        unfiltered_matched_normal_bam = (
            File.objects.filter(file_name__startswith=patient_normals_search, 
                                file_name__endswith=IGO_UNFILTERED_REGEX
                                )
            .order_by("-created_date")
            .first()
        )
        
        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(".bam")

    # Case 4
    if not unfiltered_matched_normal_bam:
        warnings.append(
            "WARNING: Could not find matching IGO unfiltered normal bam file for patient {}. "
            "Searching for DMP ACCESS sample."
        )
        unfiltered_matched_normal_bam = (
            FileMetadata.objects.filter(
                file__file_group=DMP_FILE_GROUP,
                metadata__patient__cmo=patient_id.lstrip("C-"),
                metadata__type="N",
                metadata__assay='XS2',
                file__path__endswith=DMP_REGEX,
            )
            .order_by("-metadata__imported")
            .first()
        )
        if not unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = (
                FileMetadata.objects.filter(
                    file__file_group=DMP_FILE_GROUP,
                    metadata__patient__cmo=patient_id.lstrip("C-"),
                    metadata__type="N",
                    metadata__assay='XS1',
                    file__path__endswith=DMP_REGEX,
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

    # Case 6
    if not unfiltered_matched_normal_bam:
        warnings.append(
            "WARNING: Could not find DMP or IGO matching unfiltered normal bam file for patient {}. "
            "We will skip matched normal genotyping for this sample."
        )

        unfiltered_matched_normal_bam = None
        unfiltered_matched_normal_sample_id = ""
    
    for msg in warnings:
        msg = msg.format(patient_id)

    return unfiltered_matched_normal_bam, unfiltered_matched_normal_sample_id


def get_normal_geno_samples(tumor_sample_id, matched_normal_unfiltered_id, fillout_unfiltered_normals):
    """
    20 first Normal fillout samples

    :return:
    """
    geno_samples_normal_unfiltered = fillout_unfiltered_normals[:20]
    patient_id = "-".join(tumor_sample_id.split("-")[0:2])
    if len(geno_samples_normal_unfiltered) < 20:
        fillout_unfiltered_normals_ids = [s.file_name.replace(UNCOLLAPSED_BAM_STEM, "") for s in geno_samples_normal_unfiltered]
        patient_normals_search = patient_id + NORMAL_SAMPLE_SEARCH
        study_level_normals = list(
            File.objects.filter(file_name__startswith=patient_normals_search, 
                                file_name__endswith=IGO_UNFILTERED_REGEX,
                                port__run__tags__igoRequestId__startswith=request_id.split("_")[0]
                                ).exclude(file_name__in=fillout_unfiltered_normals_ids).all()
        )
        geno_samples_normal_unfiltered = geno_samples_normal_unfiltered + study_level_normals
    LOGGER.info(
        "Adding {} fillout samples to Nucleovar run for sample {}:".format(
            len(geno_samples_normal_unfiltered), tumor_sample_id
        )
    )
    LOGGER.info([s.file_name for s in geno_samples_normal_unfiltered])

    # Exclude matched normal bam
    if matched_normal_unfiltered_id:
        geno_samples_normal_unfiltered = [
            s for s in geno_samples_normal_unfiltered if not s.file_name.startswith(matched_normal_unfiltered_id)
        ]
    geno_samples_normal_unfiltered_sample_ids = [s.file_name.replace(UNCOLLAPSED_BAM_STEM, "") for s in geno_samples_normal_unfiltered]
    return geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids


def get_geno_samples(tumor_sample_id, matched_normal_id, fillout_simplex_tumors, fillout_duplex_tumors):
    """
    Use the initial fastq metadata to get the capture of the sample,
    then, based on this capture ID, find tumor and matched normal simplex and duplex bams for genotyping

    Also include any tumor samples from the same patient

    Limits to 40 samples (or 80 bams, because each has Simplex and Duplex)

    Todo: put metadata on the Bams themselves

    :param tumor_sample_id: str
    :return:
    """

    # Get capture ID
    capture_id = None
    sample_ids = []
    sample_fastq = FileRepository.filter(
        file_type="fastq", metadata={settings.CMO_SAMPLE_NAME_METADATA_KEY: tumor_sample_id}, filter_redact=True
    )
    if len(sample_fastq) >= 1:
        capture_id = sample_fastq[0].metadata["captureName"]

        if capture_id:
            # Get samples IDs from this capture from fastqs with this capture ID
            sample_id_fastqs = FileRepository.filter(
                file_type="fastq", metadata={"captureName": capture_id}, filter_redact=True
            )
            sample_ids = list(set([f.metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] for f in sample_id_fastqs]))
            # Don't double-genotype the main sample
            sample_ids.remove(tumor_sample_id)
    
    if len(sample_ids) == 0 or not capture_id:
        duplex_capture_samples = []
        simplex_capture_samples = []
    else:
        capture_q = Q(*[("file_name__startswith", id) for id in sample_ids], _connector=Q.OR)
        duplex_capture_q = Q(file_name__endswith=DUPLEX_BAM_SEARCH) & capture_q
        simplex_capture_q = Q(file_name__endswith=SIMPLEX_BAM_SEARCH) & capture_q

        duplex_capture_samples = (
            File.objects.filter(duplex_capture_q)
            .distinct("file_name")
            .order_by("file_name", "-created_date")
            .exclude(file_name__startswith=tumor_sample_id)
            .exclude(file_name__startswith=matched_normal_id)
        )
        simplex_capture_samples = (
            File.objects.filter(simplex_capture_q)
            .distinct("file_name")
            .order_by("file_name", "-created_date")
            .exclude(file_name=tumor_sample_id)
            .exclude(file_name__startswith=matched_normal_id)
        )

        duplex_capture_samples = list(duplex_capture_samples)
        simplex_capture_samples = list(simplex_capture_samples)
    # Add patient matched Tumors samples
    patient_id = "-".join(tumor_sample_id.split("-")[0:2])
    matched_tumor_search = patient_id + TUMOR_SAMPLE_SEARCH
    duplex_matched_q = Q(file_name__endswith=DUPLEX_BAM_SEARCH) & Q(file_name__startswith=matched_tumor_search)
    simplex_matched_q = Q(file_name__endswith=SIMPLEX_BAM_SEARCH) & Q(file_name__startswith=matched_tumor_search)

    duplex_matched_samples = (
        File.objects.filter(duplex_matched_q)
        .distinct("file_name")
        .order_by("file_name", "-created_date")
        .exclude(file_name__startswith=tumor_sample_id)
        .exclude(file_name__startswith=matched_normal_id)
    )
    simplex_matched_samples = (
        File.objects.filter(simplex_matched_q)
        .distinct("file_name")
        .order_by("file_name", "-created_date")
        .exclude(file_name__startswith=tumor_sample_id)
        .exclude(file_name__startswith=matched_normal_id)
    )

    duplex_geno_samples = list(duplex_matched_samples) + list(duplex_capture_samples)
    simplex_geno_samples = list(simplex_matched_samples) + list(simplex_capture_samples)
    if len(duplex_geno_samples) < 20:
        num_geno_samples_to_add = 20 - len(duplex_geno_samples)
        duplex_geno_samples_to_add = fillout_duplex_tumors[:num_geno_samples_to_add]
        simplex_geno_samples_to_add = fillout_simplex_tumors[:num_geno_samples_to_add]
        # Remove the main tumor sample
        duplex_geno_samples_to_add = [s for s in duplex_geno_samples_to_add if s.file_name.replace(DUPLEX_BAM_STEM, "") != tumor_sample_id
        ]
        simplex_geno_samples_to_add = [s for s in simplex_geno_samples_to_add if s.file_name.replace(SIMPLEX_BAM_STEM, "") != tumor_sample_id]
        duplex_geno_samples += duplex_geno_samples_to_add
        simplex_geno_samples += simplex_geno_samples_to_add

    # Deduplicate based on PK
    duplex_geno_samples = list(set(duplex_geno_samples))
    simplex_geno_samples = list(set(simplex_geno_samples))
    # Deduplicate based on file name
    duplex_geno_samples, simplex_geno_samples = _remove_dups_by_file_name(
        duplex_geno_samples, simplex_geno_samples
    )

    return duplex_geno_samples, simplex_geno_samples

def get_dmp_matched_patient_geno_samples(patient_id):
    """
    Find DMP ACCESS samples for genotyping

    :param patient_id: str - CMO sample ID (C-123ABC)
    :return: (QuerySet<File> - Duplex Bams, QuerySet<File> - Simplex Bams, str[] duplex samples IDs,
        str[] simplex sample IDs)
    """
    matched_tumors_dmp = FileMetadata.objects.filter(
                file__file_group=DMP_FILE_GROUP,
                metadata__patient__cmo=patient_id.lstrip("C-"),
                metadata__assay='XS2',
                metadata__type="T",
                file__path__endswith=DMP_REGEX,
            )
    if not matched_tumors_dmp:
            matched_tumors_dmp = FileMetadata.objects.filter(
                file__file_group=DMP_FILE_GROUP,
                metadata__patient__cmo=patient_id.lstrip("C-"),
                metadata__assay='XS1',
                metadata__type="T",
                file__path__endswith=DMP_REGEX,
            )
    matched_tumors_dmp_simplex = [b.file for b in matched_tumors_dmp]
    matched_tumors_dmp_duplex = copy.deepcopy(matched_tumors_dmp_simplex)
    
    for d in matched_tumors_dmp_duplex:
        d.file_name = d.file_name.replace('-standard', '-duplex')
    for s in matched_tumors_dmp_simplex:
        s.file_name = s.file_name.replace('-standard', '-simplex')
    return (
        matched_tumors_dmp_duplex,
        matched_tumors_dmp_simplex
    )
class NucleoVarOperator(Operator):


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

    
    def find_curated_normal_bams():
        """
        Find curated normal bams from access curated bam file group

        :return: list of curated normal bams 
        """  
        # Cache a set of fillout bams from this request for genotyping (we only need to do this query once)
        curated_normals_metadata = FileMetadata.objects.filter(
            file__file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG
        )
        curated_normal_bams = [f.file for f in curated_normals_metadata]
        d,s = split_duplex_simplex(curated_normal_bams)
        curated_normal_bams = make_pairs(d, s)
        return curated_normal_bams
    
    def create_sample_info(tumor_sample_id, patient_id, fillout_unfiltered_normals, fillout_simplex_tumors, fillout_duplex_tumors):
        """
        Query DB for all relevant files / metadata necessary for SNV pipeline input:

        - Tumor Duplex Bam
        - Tumor Simplex Bam
        - Matched Normal Unfiltered bam (from IGO / DMP or None) (external code)
        - Other Tumor Duplex bams from same patient or capture (for genotyping)
        - Other Tumor Simplex bams from same patient or capture (for genotyping)

        :return:
        """
        # Get the Matched, Unfiltered, Normal BAM
        matched_normal_unfiltered_bam, matched_normal_unfiltered_id = get_unfiltered_matched_normal(patient_id, fillout_unfiltered_normals, request_id)

        # Get genotyping bams for Unfiltered Normal samples from the same Study
        geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids = get_normal_geno_samples(
            tumor_sample_id, matched_normal_unfiltered_id, fillout_unfiltered_normals
        )
        # Get genotyping bams for Simplex and Duplex Tumor samples from the same Patient or in the same Capture
        geno_samples_duplex, geno_samples_simplex = get_geno_samples(
            tumor_sample_id, matched_normal_unfiltered_id, fillout_simplex_tumors, fillout_duplex_tumors
        )
        capture_samples_duplex_sample_ids = [s.file_name.replace(DUPLEX_BAM_STEM, "") for s in geno_samples_duplex]
        
        capture_samples_simplex_sample_ids = [s.file_name.replace(SIMPLEX_BAM_STEM, "") for s in geno_samples_simplex]
        # Use sample IDs to remove duplicates from normal geno samples
        geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids = _remove_normal_dups(
            geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids, capture_samples_duplex_sample_ids
        )
        # SNV pipeline requires that all samples have simplex and duplex bams
        if set(capture_samples_duplex_sample_ids) != set(capture_samples_simplex_sample_ids):
            msg = "ACCESS SNV Operator Error: Duplex sample IDs not matched to Simplex sample IDs"
            raise Exception(msg)
        # Add in any DMP ACCESS samples
        (
            dmp_matched_tumors_duplex,
            dmp_matched_tumors_simplex
        ) = get_dmp_matched_patient_geno_samples(patient_id)
        geno_samples_duplex = geno_samples_duplex + dmp_matched_tumors_duplex
        geno_samples_simplex = geno_samples_simplex + dmp_matched_tumors_simplex
        geno_samples = make_pairs(geno_samples_duplex, geno_samples_simplex)
        sample_info = {
            "matched_normal_unfiltered": [matched_normal_unfiltered_bam],
            "geno_samples": geno_samples,
            "geno_samples_normal_unfiltered": geno_samples_normal_unfiltered,
        }

        return sample_info
    
    def mapping_bams(sample_info):
        # sample_id,normal_path,duplex_path,simplex_path,type
        # patient_id,sample_id,type,maf,standard_bam,standard_bai,duplex_bam,duplex_bai,simplex_bam,simplex_bai
        bams = []
        aux_bams = []
        for key, value in sample_info.items():
            for v in value: 
                map = {}
                if key == 'tumor_bam':
                    map['patient_id'] = ''
                    map['sample_id'] =  v[0].file_name.replace(DUPLEX_BAM_STEM, '') 
                    map['maf'] = ''
                    map['standard_bam'] = ''
                    map['standard_bai'] = ''
                    map['duplex_bam'] = _create_cwl_bam_object(v[0].path)
                    map['duplex_bai'] = _create_cwl_bam_object(v[0].path.replace('bam','bai'))
                    map['simplex_bam'] = _create_cwl_bam_object(v[1].path)
                    map['simplex_bai'] = _create_cwl_bam_object(v[1].path.replace('bam','bai'))
                    map['type'] = 'CASE'
                    bams.append(map)
                if key == 'normal_bam':
                    map['patient_id'] = ''
                    map['sample_id'] =  v.file_name.replace(UNCOLLAPSED_BAM_STEM, "")
                    map['maf'] = ''
                    map['standard_bam'] = _create_cwl_bam_object(v.path)
                    map['standard_bai'] = _create_cwl_bam_object(v.path.replace('bam','bai'))
                    map['duplex_bam'] = ''
                    map['duplex_bai'] = ''
                    map['simplex_bam'] = ''
                    map['simplex_bai'] = ''
                    map['type'] = 'CONTROL'
                    bams.append(map)
                if key == 'geno_samples':
                    map['sample_id'] =  v[0].file_name.replace(DUPLEX_BAM_STEM, "")
                    map['normal_path'] = ''
                    map['duplex_path'] = _create_cwl_bam_object(v[0].path)
                    map['simplex_path'] = _create_cwl_bam_object(v[1].path)
                    map['type'] = 'PLASMA'
                    aux_bams.append(map)
                if key == 'geno_samples_normal_unfiltered':
                    map['sample_id'] =  v.file_name.replace(UNCOLLAPSED_BAM_STEM, "")
                    map['normal_path'] = _create_cwl_bam_object(v.path)
                    map['duplex_path'] = ''
                    map['simplex_path'] = ''
                    map['type'] = 'UNMATCHED_NORMAL'
                    aux_bams.append(map)
                if key == 'matched_normal_unfiltered':
                    map['sample_id'] =  v.file_name.replace(UNCOLLAPSED_BAM_STEM, "")
                    map['normal_path'] = _create_cwl_bam_object(v.path)
                    map['duplex_path'] = ''
                    map['simplex_path'] = ''
                    map['type'] = 'MATCHED_NORMAL'
                    aux_bams.append(map)
        bams = {
                "input": bams,
            }
        aux_bams = {
                "aux_bams": aux_bams,
            }
        return(bams, aux_bams)
    

    def get_request_id_runs(self, app):
        """
        Get the latest completed bam-generation runs for the given request ID

        :param request_id: str - IGO request ID
        :return: List[str] - List of most recent runs from given request ID
        """
        # if not request_id:
        #         request_id_runs = Run.objects.filter(pk__in=self.run_ids)
        #         self.request_id = most_recent_runs_for_request[0].tags["igoRequestId"]
        # else: 
        operator_run_id = (
            Run.objects.filter(
                tags__igoRequestId=self.request_id,
                app__name__in=app,
                operator_run__status=RunStatus.COMPLETED,
            )
            .exclude(finished_date__isnull=True)
            .order_by("-finished_date")
            .first()
            .operator_run_id
        )

        request_id_runs = Run.objects.filter(
            operator_run_id=operator_run_id, app__name__in=app, status=RunStatus.COMPLETED
        )
        return request_id_runs
    
    def get_jobs(self):
        """
        get_job information tor run NucleoVar Pipeline
        - self: NucleoVarOperator(Operator)

        :return: return RunCreator Objects with NucleoVar information
        """
        # Run Information
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = pipeline.output_directory
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        # If no request_id, get request id from run information
        # else request_id given directly
        if not self.request_id:
            most_recent_runs_for_request = Run.objects.filter(pk__in=self.run_ids)
            self.request_id = most_recent_runs_for_request[0].tags["igoRequestId"]
        else:
            runs = self.get_request_id_runs( ["access v2 nucleo", "access legacy"])
        
        # TUMOR AND NORMAL BAMS from the request access v2 nucleo run
        bams = []
        for run in runs:
            bams.append(self.find_request_bams(run))

        # TUMOR
        tumor_bams = [(b['fgbio_filter_consensus_reads_duplex_bam'], b['fgbio_postprocessing_simplex_bam']) for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_duplex_bam'].file_name)]
        
        # FILLOUT NORMAL AND TUMOR 
        fillout_simplex_tumors = [b['fgbio_postprocessing_simplex_bam'] for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_simplex_bam'].file_name)]
        fillout_duplex_tumors = [b['fgbio_filter_consensus_reads_duplex_bam'] for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_simplex_bam'].file_name)]
        fillout_unfiltered_normals = [b['uncollapsed_bam'] for b in bams if not self.is_tumor_bam(b['uncollapsed_bam'].file_name)]
        
        # NORMAL BAM
        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME)[0]
        
        # CURATED NORMAL
        curated_normal_bams = self.find_curated_normal_bams()

        # SAMPLE INFO 
        sample_infos = []
        for d, s in tumor_bams:
            tumor_sample_id = d.file_name.replace(DUPLEX_BAM_STEM, "")
            patient_id = "-".join(tumor_sample_id.split("-")[0:2])
            sample_info = self.create_sample_info(tumor_sample_id, patient_id, fillout_unfiltered_normals, fillout_simplex_tumors, fillout_duplex_tumors)
            sample_info["normal_bam"] = [normal_bam]
            sample_info["tumor_bam"] = [(d, s)]
            sample_infos.append(sample_info)

        # Build Ridgeback Jobs from Sample Info
        # One job per Sample
        jobs = []
        for s in sample_infos:
            sample = d.file_name.replace(DUPLEX_BAM_STEM, "")
            patient_id = "-".join(sample.split("-")[0:2])
            bams, aux_bams = self.mapping_bams(s)
            input_json = {
                "input": bams,
                "aux_bams": aux_bams,
                "fasta": "/juno/work/access/production/resources/reference/current/Homo_sapiens_assembly19.fasta",
                "fai": "/juno/work/access/production/resources/reference/current/Homo_sapiens_assembly19.fasta.fai",
                "dict": "/juno/work/access/production/resources/reference/current/Homo_sapiens_assembly19.dict",
                "canonical_bed": "/juno/work/access/production/resources/msk-access/v1.0/regions_of_interest/versions/v1.0/MSK-ACCESS-v1_0panelA_canonicaltargets_500buffer.bed",
                "target_bed": '/juno/work/access/production/resources/msk-access/v1.0/regions_of_interest/versions/v1.0/MSK-ACCESS-v1_0panelA_canonicaltargets_500buffer.bed',
                "rules_json": "/juno/work/access/production/resources/nucleovar/rules.json",
                "header_file": '/juno/work/access/production/resources/nucleovar/mutect_annotate_concat_header.txt',
                "sample_order_file": '',
                "blocklist": "/juno/work/access/production/resources/nucleovar/access_blocklist.txt",
                "canonical_tx_ref": "/juno/work/access/production/resources/nucleovar/canonical_target_tx_ref.tsv"

            }
            sample_metadata = {
                    settings.PATIENT_ID_METADATA_KEY: patient_id,
                    settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: sample,
            }
            job_tags = {
                    "pipeline": pipeline.name,
                    "pipeline_version": pipeline.version,
                    settings.PATIENT_ID_METADATA_KEY: patient_id,
                    settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: sample,
            }
            job_json = {
                "name": "Nucleovar {sample}: {run_date}".format(sample=sample, run_date=run_date),
                "app": app,
                "inputs": input_json,
                "tags": job_tags,
                "output_directory": output_directory,
                "output_metadata": sample_metadata
            }
            jobs.append(job_json)
        return [RunCreator(**job) for job in jobs]
    