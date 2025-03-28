import os, sys
import re
import json
import logging
from pprint import pprint
from django.conf import settings
from .bin.make_sample import remove_with_caveats
from .bin.pair_request import compile_pairs
from file_system.repository.file_repository import FileRepository

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)


PDX_SPECIMEN_TYPES = ["pdx", "xenograft", "xenograftderivedcellline"]
NON_PDX_SPECIMEN_TYPES = [
    "biopsy",
    "blood",
    "cellLine",
    "cfdna",
    "fingernails",
    "nonpdx",
    "normal",
    "organoid",
    "other",
    "rapidautopsy",
    "resection",
    "saliva",
    "tumor",
    "poolednormal",
    "dmp",
]

# TODO: generalize
def load_references():
    d = json.load(open(os.path.join(WORKDIR, "reference_jsons/genomic_resources.json"), "rb"))
    return d


# TODO: obsolete this once Argos has been in production for a while
def calculate_abra_ram_size(grouping_dict):
    return


def normalize_igo_text_field(igo_text):
    # Flatten text data from the Genomics Core
    # to allow robust exact text matching.
    #
    # Allow variance in case and ignore non
    # alphanumeric characters (FYI).
    # Convert to lowercase
    s = igo_text.lower()
    # Remove special characters and extra spaces
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


# TODO: This is ARGOS-formatted, note the confusing IDs
def format_sample(data, specimen_type):
    sample = dict()
    sample["ID"] = data["SM"]  # TODO: change someday
    sample["CN"] = data["CN"]
    sample["LB"] = data["LB"]
    sample["PL"] = data["PL"]
    sample["PU"] = data["PU"]
    sample["R1"] = list()
    sample["R2"] = list()
    sample["zR1"] = list()  # TODO: Add for Xenografts
    sample["zR2"] = list()  # TODO: Add for Xenografts
    sample["bam"] = list()
    sample["zBam"] = list()
    sample["RG_ID"] = data["ID"]
    sample["adapter"] = "AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATGAGCATCTCGTATGCCGTCTTCTGCTTG"
    sample["adapter2"] = "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT"
    sample["bwa_output"] = sample["ID"] + ".bam"
    sample["request_id"] = data["request_id"]
    sample["specimen_type"] = data["specimen_type"]

    if specimen_type in PDX_SPECIMEN_TYPES:
        r1 = "zR1"
        r2 = "zR2"
        bam = "zBam"
    elif specimen_type in NON_PDX_SPECIMEN_TYPES:
        r1 = "R1"
        r2 = "R2"
        bam = "bam"
    else:
        raise Exception(f"Invalid Specimen Type: {specimen_type}")

    for i in data["R1"]:
        if i:
            sample[r1].append({"class": "File", "location": "juno://" + i})
    for i in data["R2"]:
        if i:
            sample[r2].append({"class": "File", "location": "juno://" + i})
    for i in data["bam"]:
        if i:
            sample[bam].append({"class": "File", "location": "juno://" + i})
    return sample


def construct_argos_jobs(samples, pairs=None, logger=None):
    samples, error_samples = remove_with_caveats(samples)
    pairs = compile_pairs(samples, pairs, logger=logger)
    number_of_tumors = len(pairs["tumor"])
    argos_jobs = list()
    for i in range(0, number_of_tumors):
        tumor = pairs["tumor"][i]
        normal = pairs["normal"][i]
        project_id = tumor["request_id"]
        assay = tumor["bait_set"]
        patient_id = tumor["patient_id"]
        pi = tumor["pi"]
        pi_email = tumor["pi_email"]
        job = dict()
        tumor_specimen_type = normalize_igo_text_field(pairs["tumor"][i]["specimen_type"])
        normal_sample = format_sample(normal, tumor_specimen_type)
        tumor_sample = format_sample(tumor, tumor_specimen_type)
        job["tumor"] = tumor_sample
        job["normal"] = normal_sample
        job["assay"] = assay
        job["pi"] = pi
        job["pi_email"] = pi_email
        job["patient_id"] = patient_id
        references = convert_references(project_id, assay, pi, pi_email)
        job.update(references)
        argos_jobs.append(job)
    return argos_jobs, error_samples


def get_curated_bams(assay, request_files):
    # Default to AgilentExon_51MB_b37_v3 BAMs for all assays except those specified below
    json_curated_bams = request_files["curated_bams"]["AgilentExon_51MB_b37_v3"]

    if assay.find("IMPACT-Heme") > -1:
        json_curated_bams = request_files["curated_bams"]["IMPACT-Heme_v2_BAITS"]
    # Default to IMPACT468_b37 BAMs for all IMPACT/HemePACT assays
    elif assay.find("IMPACT") > -1 or assay.find("HemePACT") > -1:
        json_curated_bams = request_files["curated_bams"]["IMPACT468_b37"]
    elif assay.find("IDT_Exome_v1_FP") > -1:
        json_curated_bams = request_files["curated_bams"]["IDT_Exome_v1_FP_b37"]
    array = []
    for bam in json_curated_bams:
        array.append({"class": "File", "location": str(bam)})
    return array


def get_baits_and_targets(assay, genomic_resources):
    # probably need similar rules for whatever "Exome" string is in rquest
    targets = genomic_resources["targets"]

    target_assay = assay

    if assay.find("HemePACT_v4") > -1:
        target_assay = "HemePACT_v4_BAITS"

    if assay.find("IMPACT-Heme_v2") > -1:
        target_assay = "IMPACT-Heme_v2_BAITS"

    if assay.find("IMPACT505") > -1:
        target_assay = "IMPACT505_b37"
    if assay.find("IMPACT410") > -1:
        target_assay = "IMPACT410_b37"
    if assay.find("IMPACT468") > -1:
        target_assay = "IMPACT468_b37"
    if assay.find("IMPACT341") > -1:
        target_assay = "IMPACT341_b37"
    if assay.find("IDT_Exome_v1_FP") > -1:
        target_assay = "IDT_Exome_v1_FP_b37"
    if assay.find("IMPACT468+08390") > -1:
        target_assay = "IMPACT468_08390"
    if assay.find("IMPACT468+Poirier_RB1_intron_V2") > -1:
        target_assay = "IMPACT468_08050"

    if target_assay in targets:
        return {
            "bait_intervals": {"class": "File", "location": str(targets[target_assay]["baits_list"])},
            "target_intervals": {"class": "File", "location": str(targets[target_assay]["targets_list"])},
            "fp_intervals": {"class": "File", "location": str(targets[target_assay]["FP_intervals"])},
            "fp_genotypes": {"class": "File", "location": str(targets[target_assay]["FP_genotypes"])},
        }
    else:
        LOGGER.error("ERROR: Targets for Assay not found in genomic_resources.json: %s", assay)


def get_facets_cval(assay):
    if assay.find("IMPACT") > -1 or assay.find("HemePACT") > -1:
        return 50
    return 100


def get_facets_pcval(assay):
    if assay.find("IMPACT") > -1 or assay.find("HemePACT") > -1:
        return 100
    return 500


def get_complex_nn(assay):
    if assay.find("IMPACT") > -1 or assay.find("HemePACT") > -1:
        return 0.2
    return 0.1


def get_complex_tn(assay):
    if assay.find("IMPACT") > -1 or assay.find("HemePACT") > -1:
        return 0.5
    return 0.2


def convert_references(project_id, assay, pi, pi_email):
    genomic_resources = load_references()
    request_files = genomic_resources["request_files"]
    intervals = get_baits_and_targets(assay, genomic_resources)
    curated_bams = get_curated_bams(assay, request_files)
    covariates = ["CycleCovariate", "ContextCovariate", "ReadGroupCovariate", "QualityScoreCovariate"]
    rf = ["BadCigar"]
    genome = "GRCh37"
    delly_type = ["DUP", "DEL", "INV", "INS", "BND"]
    facets_cval = get_facets_cval(assay)
    facets_pcval = get_facets_pcval(assay)
    complex_nn = get_complex_nn(assay)
    complex_tn = get_complex_tn(assay)
    temp_dir = "/scratch"
    if "TMPDIR" in os.environ:
        if os.environ["TMPDIR"]:
            temp_dir = os.environ["TMPDIR"]

    files = {
        "refseq": {"class": "File", "location": str(request_files["refseq"])},
        "vep_data": str(request_files["vep_data"]),
        "hotspot_list": str(request_files["hotspot_list"]),
        "hotspot_list_maf": {"class": "File", "location": str(request_files["hotspot_list_maf"])},
        "delly_exclude": {"class": "File", "location": str(genomic_resources["genomes"][genome]["delly"])},
        "hotspot_vcf": str(request_files["hotspot_vcf"]),
        "facets_snps": {"class": "File", "location": str(genomic_resources["genomes"][genome]["facets_snps"])},
        "custom_enst": str(request_files["custom_enst"]),
        "vep_path": str(request_files["vep_path"]),
        "conpair_markers": str(request_files["conpair_markers"]),
        "conpair_markers_bed": str(request_files["conpair_markers_bed"]),
    }

    files.update(intervals)

    out_dict = {
        "curated_bams": curated_bams,
        "hapmap": {"class": "File", "location": str(request_files["hapmap"])},
        "dbsnp": {"class": "File", "location": str(request_files["dbsnp"])},
        "indels_1000g": {"class": "File", "location": str(request_files["indels_1000g"])},
        "snps_1000g": {"class": "File", "location": str(request_files["snps_1000g"])},
        "cosmic": {"class": "File", "location": str(request_files["cosmic"])},
        "exac_filter": {"class": "File", "location": str(request_files["exac_filter"])},
        "ref_fasta": {"class": "File", "location": str(request_files["ref_fasta"])},
        "mouse_fasta": {"class": "File", "location": str(request_files["mouse_fasta"])},
        "db_files": files,
    }
    # emit_original_quals boolean could be problematic; test
    params = {
        "abra_scratch": temp_dir,
        "abra_ram_min": 84000,
        "genome": genome,
        "intervals": genomic_resources["genomes"][genome]["intervals"],
        "mutect_dcov": 50000,
        "mutect_rf": rf,
        "num_cpu_threads_per_data_thread": 6,
        "covariates": covariates,
        "emit_original_quals": True,
        "num_threads": 10,
        "assay": assay,
        "tmp_dir": temp_dir,
        "project_prefix": project_id,
        "opt_dup_pix_dist": "2500",
        "delly_type": delly_type,
        "facets_cval": facets_cval,
        "facets_pcval": facets_pcval,
        "complex_nn": complex_nn,
        "complex_tn": complex_tn,
        "scripts_bin": "/usr/bin",
        "gatk_jar_path": "/usr/bin/gatk.jar",
        "pi": pi,
        "pi_email": pi_email,
    }
    out_dict.update({"runparams": params})
    return out_dict


def get_project_prefix(request_id):
    project_prefix = set()
    tumors = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id, "tumorOrNormal": "Tumor"},
        filter_redact=True,
        values_metadata=settings.REQUEST_ID_METADATA_KEY,
    )
    for tumor in tumors:
        project_prefix.add(tumor)
    return "_".join(sorted(project_prefix))


if __name__ == "__main__":
    request_id = sys.argv[1]

    argos_jobs = construct_argos_jobs(request_id)
    pprint(argos_jobs)
