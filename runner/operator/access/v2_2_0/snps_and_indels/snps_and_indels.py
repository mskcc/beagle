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
from file_system.models import File, FileGroup, FileType
from jinja2 import Template
from runner.operator.access import get_request_id_runs, is_tumor_bam

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)
ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = "accessv2_curated_normals"
ACCESS_DEFAULT_NORMAL_ID = "Donor19F21c2206-TP01_ACCESSv2-VAL-20230004R"
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
UNCOLLAPSED_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR.bam"
ACCESS_DEFAULT_NORMAL_FILENAME_DUPLEX = (
    "Donor19F21c2206-TP01_ACCESSv2-VAL-20230004R_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
)
ACCESS_DEFAULT_NORMAL_FILENAME_SIMPLEX = (
    "Donor19F21c2206-TP01_ACCESSv2-VAL-20230004R_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-simplex.bam"
)


def check_genotype_list(genotyping_bams, genotyping_bams_ids):
    if len(genotyping_bams_ids) != len(genotyping_bams):
        raise Exception(
            f"list of genotyping bams: {genotyping_bams} is a different length from list of genotyping ids {genotyping_bams_ids}"
        )
    for ix in range(len(genotyping_bams_ids)):
        id = genotyping_bams_ids[ix].replace("-CURATED", "").replace("-DUPLEX", "").replace("-SIMPLEX", "")
        bam = genotyping_bams[ix]["location"]
        if id not in bam:
            raise Exception(f"Sample ID, {id} does not match bam path: {bam}")
    return True


def register_file(file):
    fname = os.path.basename(file)
    file_group = FileGroup.objects.get(id=DMP_FILE_GROUP)
    file_type = FileType.objects.get(name="bam")
    try:
        os.chmod(file, 0o777)
        f = File(file_name=fname, path=file, file_type=file_type, file_group=file_group)
        f.save()
        return ()
    except Exception as e:
        return ()


def _create_cwl_bam_object(bam):
    """
    Util function to create a simple CWL File object from a bam with a path attribute

    :param bam:
    :return:
    """
    return {"class": "File", "location": "iris://" + bam}


def _remove_dups_by_file_name(duplex_geno_samples, simplex_geno_samples):
    """
    Simple util to avoid Genotyping same sample twice
    (when bams come from different runs and can't be
    de-duplicated based on PK)

    :return:
    """
    duplex_geno_samples_dedup_ids = set()
    duplex_geno_samples_dedup = []
    for s in duplex_geno_samples:
        if not s.file_name in duplex_geno_samples_dedup_ids:
            duplex_geno_samples_dedup_ids.add(s.file_name)
            duplex_geno_samples_dedup.append(s)
    simplex_geno_samples_dedup_ids = set()
    simplex_geno_samples_dedup = []
    for s in simplex_geno_samples:
        if not s.file_name in simplex_geno_samples_dedup_ids:
            simplex_geno_samples_dedup_ids.add(s.file_name)
            simplex_geno_samples_dedup.append(s)
    return duplex_geno_samples_dedup, simplex_geno_samples_dedup


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
    """
    given a list split file paths using -simplex and -duplex root
    :param files: a list of simplex/duplex file path
    :return: two lists of file paths: one for simplex, one for duplex
    """
    simplex = []
    duplex = []
    for f in files:
        if f.file_name.endswith("-simplex.bam"):
            simplex.append(f)
        if f.file_name.endswith("-duplex.bam"):
            duplex.append(f)
        else:
            ValueError("Expecting a list of duplex and simplex bams")
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
        for bam in fillout_unfiltered_normals:
            if bam.file_name.startswith(patient_normals_search):
                unfiltered_matched_normal_bam = bam
        if unfiltered_matched_normal_bam:
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.replace(
                UNCOLLAPSED_BAM_STEM, ""
            )
    # Case 2
    if not request_id or not unfiltered_matched_normal_bam:
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
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam
            unfiltered_matched_normal_sample_id = unfiltered_matched_normal_bam.file_name.rstrip(".bam")
    # Case 3
    if not request_id or not unfiltered_matched_normal_bam:
        unfiltered_matched_normal_bam = (
            File.objects.filter(file_name__startswith=patient_normals_search, file_name__endswith=IGO_UNFILTERED_REGEX)
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
                metadata__assay="XS2",
                file__path__endswith=DMP_REGEX,
            )
            .order_by("-metadata__imported")
            .first()
        )
        # if not unfiltered_matched_normal_bam:
        #     unfiltered_matched_normal_bam = (
        #         FileMetadata.objects.filter(
        #             file__file_group=DMP_FILE_GROUP,
        #             metadata__patient__cmo=patient_id.lstrip("C-"),
        #             metadata__type="N",
        #             metadata__assay="XS1",
        #             file__path__endswith=DMP_REGEX,
        #         )
        #         .order_by("-metadata__imported")
        #         .first()
        #     )
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


def get_normal_geno_samples(request_id, tumor_sample_id, matched_normal_unfiltered_id, fillout_unfiltered_normals):
    """
    20 first Normal fillout samples

    If less than 20 normal samples in the request, look for normals in the same study.

    :return:
    """
    geno_samples_normal_unfiltered = fillout_unfiltered_normals[:20]
    patient_id = "-".join(tumor_sample_id.split("-")[0:2])
    # If less than 20 normal samples in the request, look for normals in the same study
    if len(geno_samples_normal_unfiltered) < 20:
        fillout_unfiltered_normals_ids = [
            s.file_name.replace(UNCOLLAPSED_BAM_STEM, "") for s in geno_samples_normal_unfiltered
        ]
        patient_normals_search = patient_id + NORMAL_SAMPLE_SEARCH
        collected_normals = fillout_unfiltered_normals_ids + [matched_normal_unfiltered_id]
        exclude_request_normals = Q()
        for normal in collected_normals:
            exclude_request_normals |= Q(file_name__startswith=normal)
        study_search = Q(
            file_name__startswith=patient_normals_search,
            file_name__endswith=IGO_UNFILTERED_REGEX,
            port__run__tags__igoRequestId__startswith=request_id.split("_")[0],
        )
        study_level_normals = list(
            File.objects.filter(study_search)
            .distinct("file_name")
            .order_by("file_name", "-created_date")
            .exclude(file_name__startswith=tumor_sample_id)
            .exclude(exclude_request_normals)
        )
        geno_samples_normal_unfiltered = geno_samples_normal_unfiltered + study_level_normals

    LOGGER.info(
        "Adding {} fillout samples to SNV run for sample {}:".format(
            len(geno_samples_normal_unfiltered), tumor_sample_id
        )
    )

    # Exclude matched normal bam
    if matched_normal_unfiltered_id:
        geno_samples_normal_unfiltered = [
            s for s in geno_samples_normal_unfiltered if not s.file_name.startswith(matched_normal_unfiltered_id)
        ]
    geno_samples_normal_unfiltered_sample_id = [
        s.file_name.replace(UNCOLLAPSED_BAM_STEM, "") for s in geno_samples_normal_unfiltered
    ]
    return geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_id


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
        duplex_geno_samples_to_add = [
            s for s in duplex_geno_samples_to_add if s.file_name.replace(DUPLEX_BAM_STEM, "") != tumor_sample_id
        ]
        simplex_geno_samples_to_add = [
            s for s in simplex_geno_samples_to_add if s.file_name.replace(SIMPLEX_BAM_STEM, "") != tumor_sample_id
        ]
        duplex_geno_samples += duplex_geno_samples_to_add
        simplex_geno_samples += simplex_geno_samples_to_add

    # Deduplicate based on PK
    duplex_geno_samples = list(set(duplex_geno_samples))
    simplex_geno_samples = list(set(simplex_geno_samples))
    # Deduplicate based on file name
    duplex_geno_samples, simplex_geno_samples = _remove_dups_by_file_name(duplex_geno_samples, simplex_geno_samples)

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
        metadata__assay="XS2",
        metadata__type="T",
        file__path__endswith=DMP_REGEX,
    )
    matched_tumors_dmp_simplex = [b.file for b in matched_tumors_dmp]
    matched_tumors_dmp_duplex = copy.deepcopy(matched_tumors_dmp_simplex)

    for d in matched_tumors_dmp_duplex:
        d.file_name = d.file_name.replace("-standard", "-duplex")
        d.path = d.path.replace("-standard", "-duplex")
        register_file(d.path)
    for s in matched_tumors_dmp_simplex:
        s.file_name = s.file_name.replace("-standard", "-simplex")
        s.path = s.path.replace("-standard", "-simplex")
        register_file(s.path)
    return (matched_tumors_dmp_duplex, matched_tumors_dmp_simplex)


class AccessV2LegacySNV(Operator):
    def find_request_bams(self, run):
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

    def find_curated_normal_bams(self):
        """
        Find curated normal bams from access curated bam file group

        :return: list of curated normal bams
        """
        # Cache a set of fillout bams from this request for genotyping (we only need to do this query once)
        curated_normal_bams = File.objects.filter(file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG)
        d, s = split_duplex_simplex(curated_normal_bams)
        curated_normal_bams = make_pairs(d, s)
        return curated_normal_bams

    def create_sample_info(
        self,
        tumor_sample_id,
        patient_id,
        fillout_unfiltered_normals,
        fillout_simplex_tumors,
        fillout_duplex_tumors,
    ):
        """
        Query DB for all relevant files / metadata necessary for SNV pipeline input:

        - Tumor Duplex Bam
        - Tumor Simplex Bam
        - Matched Normal Unfiltered bam (from IGO / DMP or None) (external code)
        - Other Tumor Duplex bams from same patient or capture (for genotyping)
        - Other Tumor Simplex bams from same patient or capture (for genotyping)

        :return:
        """
        request_id = self.request_id
        # Get the Matched, Unfiltered, Normal BAM
        matched_normal_unfiltered_bam, matched_normal_unfiltered_id = get_unfiltered_matched_normal(
            patient_id, fillout_unfiltered_normals, request_id
        )

        # Get genotyping bams for Unfiltered Normal samples from the same Study
        geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids = get_normal_geno_samples(
            request_id, tumor_sample_id, matched_normal_unfiltered_id, fillout_unfiltered_normals
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
        # (dmp_matched_tumors_duplex, dmp_matched_tumors_simplex) = get_dmp_matched_patient_geno_samples(patient_id)

        geno_samples_duplex = geno_samples_duplex
        geno_samples_simplex = geno_samples_simplex
        geno_samples = make_pairs(geno_samples_duplex, geno_samples_simplex)
        sample_info = {
            "matched_normal_unfiltered": [matched_normal_unfiltered_bam],
            "geno_samples": geno_samples,
            "geno_samples_normal_unfiltered": geno_samples_normal_unfiltered,
        }

        return sample_info

    def construct_sample_inputs(self, sample_info):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())
            genotyping_bams = []
            genotyping_bams_ids = []
            tumor_bam_duplex = [_create_cwl_bam_object(sample_info["tumor_bam"][0][0].path)]
            tumor_bam_simplex = [_create_cwl_bam_object(sample_info["tumor_bam"][0][1].path)]
            tumor_sample_name = [sample_info["tumor_bam"][0][0].file_name.split("_")[0]]
            tumor_duplex_id = [sample_info["tumor_bam"][0][0].file_name.split("_")[0]]
            tumor_simplex_id = [sample_info["tumor_bam"][0][1].file_name.split("_")[0] + "-SIMPLEX"]

            normal_bam_duplex = [_create_cwl_bam_object(sample_info["normal_bam"][0][0].path)]
            normal_bam_simplex = [_create_cwl_bam_object(sample_info["normal_bam"][0][1].path)]
            normal_sample_name = [sample_info["normal_bam"][0][0].file_name.split("_")[0]]
            normal_duplex_id = [sample_info["normal_bam"][0][0].file_name.split("_")[0] + "-CURATED-DUPLEX"]
            normal_simplex_id = [sample_info["normal_bam"][0][1].file_name.split("_")[0] + "-CURATED-SIMPLEX"]

            genotyping_bams_ids = tumor_duplex_id + tumor_simplex_id + normal_duplex_id + normal_simplex_id

            genotyping_bams = tumor_bam_duplex + tumor_bam_simplex + normal_bam_duplex + normal_bam_simplex

            if sample_info["matched_normal_unfiltered"][0] == None:
                matched_normal_id = [""]
            else:
                matched_normal = [_create_cwl_bam_object(sample_info["matched_normal_unfiltered"][0].path)]
                matched_normal_id = [sample_info["matched_normal_unfiltered"][0].file_name.split("_")[0]]
                genotyping_bams_ids += matched_normal_id
                genotyping_bams += matched_normal

            for key, files in sample_info.items():
                for f in files:
                    if key == "geno_samples":
                        sample_id_duplex = f[0].file_name.split("_")[0]
                        sample_id_simplex = f[1].file_name.split("_")[0] + "-SIMPLEX"
                        genotyping_bams_ids.append(sample_id_duplex)
                        genotyping_bams_ids.append(sample_id_simplex)
                        genotyping_bams.append(_create_cwl_bam_object(f[0].path))
                        genotyping_bams.append(_create_cwl_bam_object(f[1].path))
                    if key == "geno_samples_normal_unfiltered":
                        sample_id = f.file_name.split("_")[0]
                        genotyping_bams_ids.append(sample_id)
                        genotyping_bams.append(_create_cwl_bam_object(f.path))
                    if key == "curated_normal_bams":
                        sample_id_duplex = f[0].file_name.split("_")[0] + "-CURATED-DUPLEX"
                        sample_id_simplex = f[1].file_name.split("_")[0] + "-CURATED-SIMPLEX"
                        genotyping_bams_ids.append(sample_id_duplex)
                        genotyping_bams_ids.append(sample_id_simplex)
                        genotyping_bams.append(_create_cwl_bam_object(f[0].path))
                        genotyping_bams.append(_create_cwl_bam_object(f[1].path))

            # check genotyping bams
            check_genotype_list(genotyping_bams, genotyping_bams_ids)

            input_file = template.render(
                tumor_bams=json.dumps(tumor_bam_duplex),
                normal_bams=json.dumps(normal_bam_duplex),
                tumor_sample_names=json.dumps(tumor_sample_name),
                normal_sample_names=json.dumps(normal_sample_name),
                matched_normal_ids=json.dumps(matched_normal_id),
                genotyping_bams=json.dumps(genotyping_bams),
                genotyping_bams_ids=json.dumps(genotyping_bams_ids),
            )

            sample_input = json.loads(input_file)
            return sample_input

    def get_jobs(self):
        """
        get_job information tor run SNV Pipeline
        - self: AccessV2LegacySNV(Operator)

        :return: return RunCreator Objects with SNV information
        """
        # Run Information
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        # output_directory = pipeline.output_directory
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        # If no request_id, get request id from run information
        # else request_id given directly
        runs, self.request_id = get_request_id_runs(
            ["access v2 nucleo", "access nucleo"], self.run_ids, self.request_id
        )
        # TUMOR AND NORMAL BAMS from the request access v2 nucleo run
        bams = []
        for run in runs:
            bams.append(self.find_request_bams(run))

        # TUMOR
        tumor_bams = [
            (b["fgbio_filter_consensus_reads_duplex_bam"], b["fgbio_postprocessing_simplex_bam"])
            for b in bams
            if is_tumor_bam(b["fgbio_filter_consensus_reads_duplex_bam"].file_name)
        ]

        # FILLOUT NORMAL AND TUMOR
        fillout_simplex_tumors = [
            b["fgbio_postprocessing_simplex_bam"]
            for b in bams
            if is_tumor_bam(b["fgbio_filter_consensus_reads_duplex_bam"].file_name)
        ]
        fillout_duplex_tumors = [
            b["fgbio_filter_consensus_reads_duplex_bam"]
            for b in bams
            if is_tumor_bam(b["fgbio_filter_consensus_reads_duplex_bam"].file_name)
        ]
        fillout_unfiltered_normals = [
            b["fgbio_collapsed_bam"] for b in bams if not is_tumor_bam(b["fgbio_collapsed_bam"].file_name)
        ]

        # NORMAL BAM
        normal_bam = (
            File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME_DUPLEX)[0],
            File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME_SIMPLEX)[0],
        )

        # CURATED NORMAL
        curated_normal_bams = self.find_curated_normal_bams()

        # SAMPLE INFO
        sample_infos = []
        for d, s in tumor_bams:
            tumor_sample_id = d.file_name.replace(DUPLEX_BAM_STEM, "")
            patient_id = "-".join(tumor_sample_id.split("-")[0:2])
            sample_info = self.create_sample_info(
                tumor_sample_id,
                patient_id,
                fillout_unfiltered_normals,
                fillout_simplex_tumors,
                fillout_duplex_tumors,
            )
            sample_info["normal_bam"] = [normal_bam]
            sample_info["curated_normal_bams"] = curated_normal_bams
            sample_info["tumor_bam"] = [(d, s)]
            sample_infos.append(sample_info)

        # Build Ridgeback Jobs from Sample Info
        # One job per Sample
        jobs = []
        for s in sample_infos:
            sample = s["tumor_bam"][0][0].file_name.replace(DUPLEX_BAM_STEM, "")
            sample_input = self.construct_sample_inputs(s)
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
                "name": "ACCESS V2 LEGACY SNV {request_id}: {run_date}".format(
                    request_id=self.request_id, run_date=run_date
                ),
                "app": app,
                "inputs": sample_input,
                "tags": job_tags,
                "output_metadata": sample_metadata,
            }
            jobs.append(job_json)
        return [RunCreator(**job) for job in jobs]
