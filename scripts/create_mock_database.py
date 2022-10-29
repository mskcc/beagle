from notifier.models import Notifier, JobGroup
from beagle_etl.models import Operator
from runner.models import Run, RunStatus, OperatorRun, TriggerAggregateConditionType, TriggerRunType, Pipeline, PortType, Port
from django.contrib.auth.models import User
from django.conf import settings
from notifier.models import Notifier
from file_system.models import FileGroup, File, FileMetadata, FileType, Sample, Request, Patient
from file_system.repository import FileRepository
from random import randint, sample, uniform
from coolname import generate, generate_slug
from faker import Faker
from faker.providers import DynamicProvider
from datetime import timedelta, datetime, tzinfo
from pytz import timezone
import uuid
import os
from pathlib import Path
import string
from celery import current_app as app
import functools
import operator
import re

NUM_INVESTIGATOR = 30
NUM_LAB_HEAD = 30
NUM_DATA_ANALYST = 30

app.conf.task_always_eager = True
EASTERN = timezone('US/Eastern')
NOW = datetime.now(EASTERN)
RUN_START = NOW - timedelta(days=365)
RUN_END = NOW
RECIPES = ["IMPACT505", "ACCESS", "CMO-CH", "HumanWholeGenome", "ShallowWGS", "WholeExome"]
#TRUE_OR_FALSE = [True, False]
MALE_OR_FEMALE = ["M", "F"]
NOTIFIER_TYPE = ["JIRA", "EMAIL"]
NORMAL_SAMPLE_TYPE = ["Adjacent Normal", "Normal"]
TUMOR_SAMPLE_TYPE = ["Adjacent Tissue", "Cell free", "Local Recurrence",
                     "Metastasis", "Primary", "Other", "Recurrence", "Tumor", "Unknown Tumor"]
NORMAL_SAMPLE_CLASS = ["Normal"]
TUMOR_SAMPLE_CLASS = ["Biopsy", "Blood", "CellLine", "cfDNA", "Exosome", "Fingernails", "NA", "Organoid", "Other", "PDX",
                      "Plasma", "RapidAutopsy", "Resection", "Saliva", "Tissue", "Tumor", "Whole Blood", "Xenograft", "XenograftDerivedCellLine"]
TUMOR_SAMPLE_ORIGIN = ["Bladder Adenocarcinoma", "Bladder Urothelial Carcinoma", "Block", "Bone Marrow Aspirate", "Buccal Swab", "Buffy Coat", "Cell Pellet", "Cells", "Cerebrospinal Fluid", "Chromophobe Renal Cell Carcinoma", "Core Biopsy", "Curls", "Cutaneous Squamous Cell Carcinoma", "Esophageal Squamous Cell Carcinoma", "FH-Deficient Renal Cell Carcinoma", "Head and Neck Carcinoma, Other", "Head and Neck Squamous Cell Carcinoma", "Head and Neck Squamous Cell Carcinoma of Unknown Primary", "Hypopharynx Squamous Cell Carcinoma", "Larynx Squamous Cell Carcinoma", "Lung Adenocarcinoma", "Lung Squamous Cell Carcinoma", "Melanoma of Unknown Primary", "Nasopharyngeal Carcinoma", "Oral Cavity Squamous Cell Carcinoma", "Organoid",
                       "Oropharynx Squamous Cell Carcinoma", "Other", "Papillary Renal Cell Carcinoma", "Plasma", "Plasmacytoid/Signet Ring Cell Bladder Carcinoma", "Punch", "Rapid Autopsy Tissue", "Renal Cell Carcinoma", "Renal Clear Cell Carcinoma", "Renal Clear Cell Carcinoma with Sarcomatoid Features", "Renal Mucinous Tubular Spindle Cell Carcinoma", "Sarcomatoid Renal Cell Carcinoma", "Sinonasal Squamous Cell Carcinoma", "Slides", "Small Cell Bladder Cancer", "Sorted Cells", "Tissue", "Translocation-Associated Renal Cell Carcinoma", "Unclassified Renal Cell Carcinoma", "Unknown", "Upper Tract Urothelial Carcinoma", "Urethral Adenocarcinoma", "Urethral Squamous Cell Carcinoma", "Urethral Urothelial Carcinoma", "Urine", "Viably Frozen Cells", "Whole Blood"]
NORMAL_SAMPLE_ORIGIN = ["Bladder Adenocarcinoma", "Bladder Urothelial Carcinoma", "Block", "blood", "Blood", "Bone Marrow Aspirate", "Buccal Swab", "Buffy Coat", "Cell Pellet", "Cells", "Cerebrospinal Fluid", "Chromophobe Renal Cell Carcinoma", "Core Biopsy", "Curls", "Cutaneous Squamous Cell Carcinoma", "Esophageal Squamous Cell Carcinoma", "FH-Deficient Renal Cell Carcinoma", "Fingernails", "Fresh Frozen Tissue", "Head and Neck Carcinoma, Other", "Head and Neck Squamous Cell Carcinoma", "Head and Neck Squamous Cell Carcinoma of Unknown Primary", "Hypopharynx Squamous Cell Carcinoma", "Larynx Squamous Cell Carcinoma", "Lung Adenocarcinoma", "Lung Squamous Cell Carcinoma", "Melanoma of Unknown Primary", "Nasopharyngeal Carcinoma", "Oral Cavity Squamous Cell Carcinoma",
                        "Organoid", "Oropharynx Squamous Cell Carcinoma", "Other", "Papillary Renal Cell Carcinoma", "Plasma", "Plasmacytoid/Signet Ring Cell Bladder Carcinoma", "Punch", "Rapid Autopsy Tissue", "Renal Cell Carcinoma", "Renal Clear Cell Carcinoma", "Renal Clear Cell Carcinoma with Sarcomatoid Features", "Renal Mucinous Tubular Spindle Cell Carcinoma", "Saliva", "Sarcomatoid Renal Cell Carcinoma", "Sinonasal Squamous Cell Carcinoma", "Slides", "Small Cell Bladder Cancer", "Sorted Cells", "Tissue", "Translocation-Associated Renal Cell Carcinoma", "Unclassified Renal Cell Carcinoma", "Unknown", "Upper Tract Urothelial Carcinoma", "Urethral Adenocarcinoma", "Urethral Squamous Cell Carcinoma", "Urethral Urothelial Carcinoma", "Urine", "Viably Frozen Cells", "Whole Blood"]
PRESERVATION = ["Blood", "Cell Pellet", "CFDNA", "CSF", "Cytology", "DMSO-ViablyFrozen",
                "EDTA-Streck", "FFPE", "Flow Cell", "Fresh", "Frozen", "OCT", "other", "Trizol"]
NORMAL_ONCO_TREE_CODE = ["", "BLCA", "CCRCC", "CHRCC", "COAD", "CSCC", "ESCC", "FHRCC", "GBAD", "HNSCUP", "HPHSC", "HS", "LUAD", "LUSC", "LXSC", "MTSCC",
                         "MUP", "NPC", "OCSC", "OHNCA", "OPHSC", "PRCC", "RCC", "SCBC", "SCCRCC", "SNSC", "SRCBC", "SRCC", "TRCC", "UAD", "UCU", "URCC", "USCC", "UTUC"]
TUMOR_ONCO_TREE_CODE = ["", "AASTR", "ACA", "ACBC", "ACC", "ACCC", "ACINAR CELL CARCINOMA OF THE PANCREAS (PAAC)", "ACPP", "ACRAL MELANOMA (ACRM)", "ACRM", "ACUTE MYELOID LEUKEMIA (AML)", "Acute Myeloid Leukemia (AML/LAML)", "ACUTE MYELOID LEUKEMIA (AML/LAML)", "ACYC", "ADNOS", "AGNG", "AIS", "AITL", "ALAL", "ALCL", "ALKLBCL", "ALL", "ALT", "ALUCA", "AML", "AMLBCRABL1", "AMLGATA2MECOM", "AMLMD", "AMLMLLT3KMT2A", "AMLMRC", "AMLNOS", "AMLNPM1", "AMLRGA", "AMLRUNX1", "AMOL", "AMPCA", "ANAPLASTIC THYROID CANCER (THAP)", "ANGL", "ANGS", "ANM", "ANSC", "AODG", "APAD", "APE", "APLPMLRARA", "APTAD", "APXA", "ARMM", "ARMS", "ASPS", "ASTR", "ATLL", "ATM", "ATRT", "BA", "BALL", "BCAC", "BCC", "B-CELL LYMPHOMA (BCL)", "BCL", "BEC", "BFN", "BGCT", "BILIARY_TRACT", "BL", "BLAD", "Bladder", "BLADDER", "Bladder Urothelial Carcinoma (BLCA)", "BLADDER UROTHELIAL CARCINOMA (BLCA)", "BLADDER_UROTHELIAL_CARCINOMA_(BLCA)", "BLCA", "BLCA)", "BLL", "BLLBCRABL1L", "BLLNOS", "BLOOD", "BLSC", "BMGCT", "BNNOS", "BONE", "BOWEL", "BPLL", "BRAIN", "BRAME", "BRCA", "BRCANOS", "BRCNOS", "BREAST", "BREAST DUCTAL CARCINOMA IN SITU (DCIS)", "BREAST INVASIVE CARCINOMA (BRCA)", "BREAST INVASIVE DUCTAL CARCINOMA (IDC)", "BREAST INVASIVE LOBULAR CARCINOMA (ILC)", "CAEXPA", "CANCER OF UNKNOWN PRIMARY (CUP)", "CCOC", "CCOV", "CCRCC", "CCS", "CEAD", "CEAS", "CECC", "CEEN", "CEMN", "CEMU", "CERVICAL ADENOCARCINOMA (CEAD)", "CERVIX", "CESC", "CHBL", "CHL", "CHOL", "CHOM", "CHOROIDAL MELANOMA (CHM)", "CHOS", "CHRCC", "CHS", "CLL", "CLLSLL", "CMC", "CML", "CMML", "CMML2", "COAD", "COADREAD", "COLON ADENOCARCINOMA (COAD)", "COLON ADENOCARCINOMA(COAD)", "COLORECTAL ADENOCARCINOMA (COADREAD)", "CPC", "CPP", "CSCC", "CSCHW", "CSCLC", "CSNOS", "CUP", "CUPNOS", "CUTANEOUS MELANOMA (SKCM)", "DA", "DASTR", "DCIS", "DDCHS", "DDLS", "DEDIFFERENTIATED LIPOSARCOMA (DDLS)", "DES", "DESM", "DFSP", "DIFFUSE LARGE B-CELL LYMPHOMA (DLBCL)", "DIFG", "DIPG", "DLBCL", "DLBCLNOS", "DSRCT", "DSTAD", "ECAD", "ECD", "EGC", "EGCT", "EHAE", "EHCH", "EMALT", "EMBC", "EMBCA", "EMCHS", "EMPD", "EMPSGC", "ENDOMETRIOID OVARIAN CANCER (EOV)", "ENKL", "EOV", "EPDCA", "EPENDYMOMA", "EPIS", "EPM", "Erdheim-Chester Disease", "ERMS", "ES", "ESCA", "ESCC", "ESOPHAGOGASTRIC ADENOCARCINOMA (EGC)", "ESS", "ET", "ETC", "ETMF", "EUC", "Extrahepatic Cholangiocarcinoma (EHCH)", "EYE", "FA", "FDCS", "FHRCC", "FIBS", "FL", "FLC", "GALLBLADDER CANCER (GBC)", "Gallbladder (GBC)", "GASTROINTESTINAL NEUROENDOCRINE TUMORS (GINET)", "GB", "GBAD", "GBC", "GBM", "GCT", "GEJ", "GINET", "GIST", "GLIOBLASTOMA MULTIFORME (GBM)", "GMN", "GN", "GNBL", "GNC", "GNOS", "GRANULOSA CELL TUMOR (GRCT)", "GRC", "GRCT", "GSARC", "HAIRY CELL LEUKEMIA (HCL)", "HCC", "HCCIHCH", "HCL", "HDCN", "Head and Neck Squamous Cell Carcinoma (HNSC)", "HEAD_NECK", "HEMA", "HEMANGIOMA (HEMA)", "HGBCL", "HGBCLMYCBCL2", "HGESS", "HGGNOS", "HGNEC", "HGNET", "HGONEC", "HGSFT", "HGSOC", "HIGH-GRADE SEROUS OVARIAN CANCER (HGSOC)", "HIST", "HL", "HNMASC", "HNMUCM", "HNNE", "HNSC", "HNSCUP", "HPHSC", "HS", "HTAT", "IAMPCA", "IDC", "IFS", "IHCH", "ILC", "IMMC", "IMT", "Intrahepatic Cholangiocarcinoma (IHCH)", "INTRAHEPATIC CHOLANGIOCARCINOMA (IHCH)", "INVASIVE BREAST CARCINOMA (BRCA)", "IPMN", "ISTAD", "JMML", "JSCB", "JXG", "KIDNEY", "LAIS", "LARGE CELL NEUROENDOCRINE CARCINOMA (LUNE)", "LCH", "LCLC", "LENTIGO MALIGNA MELANOMA (SKLMM)", "LEUK", "LGESS", "LGGNOS", "LGNET", "LGSOC", "LIAD", "LIHB", "LIPO", "LIVER", "LMS", "LNET", "LNM", "LPL", "LUACC", "LUAD",
                        "LUAS", "LUCA", "LUNE", "LUNG", "LUNG ADENOCARCINOMA (LUAD)", "LUNG ADENOCARCINOMA(LUAD)", "LUNG CARCINOID (LUCA)", "LUNG NEUROENDOCRINE TUMOR (LNET)", "LUPC", "LUSC", "LXSC", "LYMPH", "MACR", "MASC", "MBC", "MBL", "MBN", "MBT", "MCC", "MCHS", "MCL", "MDLC", "MDS", "MDS/AML", "MDSEB2", "MDS/MPN", "MDSU", "MEDULLOBLASTOMA (MBL)", "MEL", "MELANOMA (MEL)", "MELC", "MF", "MFH", "MFS", "MGCT", "MGUS", "MLYM", "MM", "MNET", "MNG", "MNM", "MOV", "MPE", "MPN", "MPNST", "MPNU", "MRC", "MRLS", "MRT", "MSTAD", "MTSCC", "MUCOSAL MELANOMA (MUM)", "MULTIPLE MYELOMA (MM)", "MUP", "MYEC", "MYELODYSPLASIA (MDS)", "MYELOID", "MYF", "MYXOFIBROSARCOMA (MFS)", "MZL", "NA", "N/A", "NBL", "NCCRCC", "NECNOS", "Neither OncoTree code nor name found for: Mixed Germ Cell Tumor(OMGCT)", "Neither OncoTree code nor name found for: Mucosal Melanoma of the Vulva/Vagina", "Neither OncoTree code nor name found for: Solitary Fibrous Tumor/Hemangiopericytoma", "NETNOS", "NFIB", "NHL", "NKCLL", "NOT", "NPC", "NSCLC", "NSCLCPD", "NSGCT", "NST", "OAST", "OCS", "OCSC", "ODG", "ODYS", "OEC", "OFMT", "OGCT", "OHNCA", "OIMT", "OM", "OMGCT", "OMT", "ONBL", "OOVC", "OPHSC", "OS", "OSACA", "OSMCA", "OSOS", "OSTEOSARCOMA (OS)", "Other", "OUSARC", "OUTT", "OVARIAN CANCER, OTHER (OOVC)", "OVARIAN EPITHELIAL CARCINOMA (OVCA)", "OVARIAN EPITHELIAL TUMOR (OVT)", "OVARY", "OVT", "OYST", "PAAC", "PAAD", "PAASC", "PACT", "PAMPCA", "PANCREAS", "PANCREATIC ADENOCARCINOMA (PAAD)", "PANET", "PAOS", "PAPILLARY THYROID CANCER (THPA)", "PAST", "PB", "PBL", "PBT", "PCGDTCL", "PCM", "PCNSL", "PCV", "PDC", "PECOMA", "PEMESO", "PERITONEUM", "PERIVASCULAR EPITHELIOID CELL TUMOR (PECOMA)", "PGNG", "PHC", "PHCH", "PLBMESO", "PLEMESO", "PLEOMORPHIC LIPOSARCOMA (PLLS)", "PLLS", "PLMESO", "PLSMESO", "PMA", "PMBL", "PMF", "PMFOFS", "PMFPES", "PNET", "PNS", "PPB", "PPTID", "PRAD", "PRCC", "PRIMARY BRAIN LYMPHOMA (PBL)", "PRNE", "PRNET", "PROLIFERATING PILAR CYSTIC TUMOR (PPCT)", "PROSTATE", "PROSTATE ACINAR ADENOCARCINOMA (PRAD)", "PROSTATE ADENOCARCINOMA (PRAD)", "PRSCC", "PSCC", "PSEC", "PT", "PTAD", "PTCA", "PTCL", "PV", "PVMF", "RBL", "RCC", "RCSNOS", "RDD", "READ", "RENAL CELL CARCINOMA (RCC)", "RMS", "ROCY", "Rosai-Dorfman Disease (RD)", "RWDNET", "SACA", "SARCL", "SARCNOS", "SBC", "SBWDNET", "SCBC", "SCCE", "SCCNOS", "SCCO", "SCCRCC", "SCHW", "SCLC", "SCRMS", "SCSRMS", "SCST", "SCUP", "SDCA", "SDCS", "SELT", "SEM", "SGAD", "SGO", "SGTTL", "SIC", "SKCM", "SKCN", "SKIN", "SKIN CUTANEOUS MELANOMA (SKCM)", "SLCT", "SM", "SMALL CELL CARCINOMA OF THE OVARY (SCCO)", "SMALL CELL LUNG CANCER (SCLC)", "SNA", "SNSC", "SNUC", "SOC", "SOFT_TISSUE", "SPDAC", "SPN", "SPTCL", "SRAP", "SRCBC", "SRCC", "SRCCR", "SSRCC", "STAD", "STOMACH", "STOMACH ADENOCARCINOMA (STAD)", "STSC", "SYNS", "TAC", "TALL", "T-ALL", "TAML", "TCCA", "TEOS", "TESTICULAR GERM CELL TUMOR (TGCT)", "TESTIS", "THAP", "THFO", "THHC", "THME", "THPA", "THPD", "THYC", "THYM", "thyroid", "THYROID", "TLL", "TMDS", "TMN", "TMT", "TNKL", "TPLL", "TRCC", "TSCST", "TSTAD", "TT", "TYST", "UAD", "UAS", "UCA", "UCCA", "UCCC", "UCEC", "UCP", "UCS", "UCU", "UDDC", "UDMN", "UEC", "ULM", "ULMS", "UM", "UM ", "UMEC", "UNK", "Unknown", "Unknown tumor", "Unknown Tumor", "UPDC", "UPPER TRACT UROTHELIAL CARCINOMA (UTUC)", "URCC", "URMM", "USARC", "USC", "USCC", "UTERINE ADENOSARCOMA (UAS)", "UTERINE ENDOMETRIOID CARCINOMA (UEC)", "UTERUS", "UTUC", "UUC", "UUS", "VDYS", "VIMT", "VMGCT", "VMM", "VMT", "VOEC", "VSC", "VULVA", "VYST", "WDLS", "WT"]
EMAIL_ADDRESS = "mskcc.org"
REFERENCE_FILES = ["known_fusions_at_mskcc.txt", "b37.fasta", "b37.fasta.fai", "microsatellites.list",
                   "curated_bam_1.bam", "curated_bam_2.bam", "curated_bam_1.bai", "curated_bam_2.bai"]
ASSAY_REFERENCE_FILES = ["{}_b37_baits.bed", "{}_b37_baits.ilist", "{}_b37_targets.bed", "{}_b37_targets.ilist",
                         "{}_fingerprint_snps.vcf", "{}_FP_tiling_genotypes.txt", "{}_FP_tiling_intervals.intervals"]
PIPELINE_PAIR_OUTPUT_FILES = ["{}.annotate-variants.vcf", "{}.combined-variants.vcf.gz", "{}.combined-variants.vcf.gz.tbi",
                              "{}.muts.maf", "{}.svs.pass.vcf", "{}.svs.pass.vep.maf", "{}.svs.pass.vep.portal.txt", "{}.svs.vcf"]
PIPELINE_SAMPLE_OUTPUT_FILES = ["{}.rg.md.asmetrics", "{}.rg.md_FP_base_counts.txt", "{}.rg.md.gcbiasmetrics", "{}.rg.md.gcbias.pdf", "{}.rg.md.gcbias.summary", "{}.rg.md.hsmetrics", "{}.rg.md.hstmetrics", "{}.rg.md.ismetrics",
                                "{}.rg.md.ismetrics.pdf", "{}.rg.md_metrics", "{}.rg.md.pileup", "{}.rg.md.abra.printreads.bai", "{}.rg.md.abra.printreads.bam", "{}.rg.md.abra.printreads.qmetrics.qcycle_metrics", "{}.rg.md.abra.printreads.qmetrics.quality_by_cycle.pdf"]
PIPELINE_QC_OUTPUT_FILES = ["{}_01_alignment.pdf", "{}_02_alignment_percentage.pdf", "{}_03_capture_specificity.pdf", "{}_04_capture_specificity_percentage.pdf", "{}_05_insert_size.pdf", "{}_06_insert_size_peaks.pdf", "{}_07_fingerprint.pdf", "{}_08_major_contamination.pdf", "{}_09_minor_contamination.pdf", "{}_11_duplication.pdf", "{}_12_library_size.pdf", "{}_13_coverage.pdf", "{}_15_base_qualities.pdf", "{}_16_gc_bias.pdf", "{}_18_minor_contam_freq_hist.pdf",
                            "{}_contamination.R", "{}_contamination.txt", "{}_DiscordantHomAlleleFractions.txt", "{}_FingerprintSummary.txt", "{}_GcBiasMetrics.txt", "{}_HsMetrics.txt", "{}_InsertSizeMetrics_Histograms.txt", "{}_MajorContamination.txt", "{}_markDuplicatesMetrics.txt", "{}_MinorContamFreqList.txt", "{}_MinorContamination.txt", "{}_post_recal_MeanQualityByCycle.txt", "{}_pre_recal_MeanQualityByCycle.txt", "{}_ProjectSummary.txt", "{}_SampleSummary.txt", "{}_QC_Report.pdf", "qcPDF.log"]
T_Or_N_list = ["Tumor", "Normal"]

POOLED_NORMAL_GROUP_NAME = "Pooled Normals"


def set_up_faker():
    Faker.seed(0)
    fake = Faker()
    INVESTIGATOR_LIST = [fake.simple_profile() for _ in range(NUM_INVESTIGATOR)]
    LAB_HEAD_LIST = [fake.simple_profile() for _ in range(NUM_LAB_HEAD)]
    DATA_ANALYST_LIST = [fake.simple_profile() for _ in range(NUM_DATA_ANALYST)]
    UPPERCASE_LETTERS = string.ascii_letters.upper()
    fake_recipe = DynamicProvider(provider_name="recipe", elements=RECIPES)
    fake_male_or_female = DynamicProvider(provider_name="male_or_female", elements=MALE_OR_FEMALE)
    fake_notifier_type = DynamicProvider(provider_name="notifier_type", elements=NOTIFIER_TYPE)
    fake_investigator_list = DynamicProvider(provider_name="investigator", elements=INVESTIGATOR_LIST)
    fake_lab_head_list = DynamicProvider(provider_name="lab_head", elements=LAB_HEAD_LIST)
    fake_data_analyst_list = DynamicProvider(provider_name="data_analyst", elements=DATA_ANALYST_LIST)
    fake_normal_sample_type = DynamicProvider(provider_name="normal_sample_type", elements=NORMAL_SAMPLE_TYPE)
    fake_tumor_sample_type = DynamicProvider(provider_name="tumor_sample_type", elements=TUMOR_SAMPLE_TYPE)
    fake_normal_sample_class = DynamicProvider(provider_name="normal_sample_class", elements=NORMAL_SAMPLE_CLASS)
    fake_tumor_sample_class = DynamicProvider(provider_name="tumor_sample_class", elements=TUMOR_SAMPLE_CLASS)
    fake_normal_sample_origin = DynamicProvider(provider_name="normal_sample_origin", elements=NORMAL_SAMPLE_ORIGIN)
    fake_tumor_sample_origin = DynamicProvider(provider_name="tumor_sample_origin", elements=TUMOR_SAMPLE_ORIGIN)
    fake_preservation = DynamicProvider(provider_name="preservation", elements=PRESERVATION)
    fake_normal_onco_tree_code = DynamicProvider(provider_name="normal_onco_tree_code", elements=NORMAL_ONCO_TREE_CODE)
    fake_tumor_onco_tree_code = DynamicProvider(provider_name="tumor_onco_tree_code", elements=TUMOR_ONCO_TREE_CODE)
    fake_letter = DynamicProvider(provider_name="uppercase_letter", elements=UPPERCASE_LETTERS)
    fake.add_provider(fake_recipe)
    fake.add_provider(fake_male_or_female)
    fake.add_provider(fake_notifier_type)
    fake.add_provider(fake_investigator_list)
    fake.add_provider(fake_lab_head_list)
    fake.add_provider(fake_data_analyst_list)
    fake.add_provider(fake_normal_sample_type)
    fake.add_provider(fake_tumor_sample_type)
    fake.add_provider(fake_normal_sample_class)
    fake.add_provider(fake_tumor_sample_class)
    fake.add_provider(fake_normal_sample_origin)
    fake.add_provider(fake_tumor_sample_origin)
    fake.add_provider(fake_preservation)
    fake.add_provider(fake_normal_onco_tree_code)
    fake.add_provider(fake_tumor_onco_tree_code)
    fake.add_provider(fake_letter)
    return fake


def create_user():
    model_user, _ = User.objects.get_or_create(
        username="shrek", email="shrek@Lord_Farquaad_stinks.org", password="Fiona")
    return model_user


def get_status():
    prob = uniform(0, 1)
    if prob <= .5:
        return RunStatus.COMPLETED
    if prob <= .55:
        return RunStatus.READY
    if prob <= .87:
        return RunStatus.RUNNING
    if prob <= .9:
        return RunStatus.FAILED
    if prob <= .95:
        return RunStatus.CREATING
    return RunStatus.ABORTED


def get_or_create_file_group(name=None):
    if not name:
        name = generate_slug()
    new_file_group, _ = FileGroup.objects.get_or_create(name=name)
    return new_file_group


def generate_length_limited_slug(num, length):
    count = 0
    limit = 20
    while True:
        slug = generate_slug(num)
        if len(slug) < length:
            return slug
        else:
            count += 1
        if count > limit:
            raise Exception("Could not find the right length slug of num {} at length {}".format(num, length))


def create_notifier(faker):
    default = faker.boolean()
    notifier_type = faker.notifier_type()
    board = "ALL"
    if notifier_type != "EMAIL":
        board = generate_length_limited_slug(2, 20)
    new_notifier = Notifier(default=default, notifier_type=notifier_type, board=board)
    new_notifier.save()
    return new_notifier


def create_new_operator(faker, recipie=None):
    if recipie:
        operator = Operator.objects.filter(recipes__contains=[recipie])
        if operator:
            return operator.first()
    slug = generate_slug()
    class_name = "runner.operator.{}.{}".format(recipie, generate_slug(2))
    version = "{}.{}.{}".format(randint(0, 9), randint(0, 9), randint(0, 9))
    if not recipie:
        recipie = faker.recipie()
    notifier = create_notifier(faker)
    new_operator = Operator(slug=slug, class_name=class_name, version=version, recipes=[recipie], notifier=notifier)
    new_operator.save()
    return new_operator


def create_pipeline(faker, recipie=None):
    name = generate_slug(3)
    if recipie:
        name = "{}-{}-pipeline".format(name, recipie)
    else:
        name = "{}-pipeline".format(name)
    github = "https://github.com/mskcc/mock_pipeline"
    version = "{}.{}.{}".format(randint(0, 9), randint(0, 9), randint(0, 9))
    entrypoint = faker.file_name(extension='cwl')
    output_file_group_name = "{}-outputs".format(recipie)
    output_file_group = get_or_create_file_group(name=output_file_group_name)
    new_operator = create_new_operator(faker, recipie=recipie)
    default = faker.boolean()
    walltime = randint(1, 1000)
    memlimit = "{}gb".format(randint(1, 100))
    new_pipeline = Pipeline(name=name, github=github, version=version, entrypoint=entrypoint,
                            output_file_group=output_file_group, operator=new_operator, default=default, walltime=walltime, memlimit=memlimit)
    new_pipeline.save()
    return new_pipeline


def create_sample_file_metadata(faker, file, user, R, sampleID, sampleName, sampleClass, sampleType, sampleOrigin, libraryId, projectName, patientName, sex, genePanel, oncoTreeCode, preservation, investigator, labHead, dataAnalyst, tumorOrNormal):
    file_metadata = {
        "R": R,
        "sex": sex,
        "ciTag": "s_C_{}_{}_d".format(patientName, sampleID),
        "runId": "PITT_0{}".format(randint(0, 100)),
        "tubeId": "{}".format(randint(100000, 999999)),
        "baitSet": "{}_BAITS".format(genePanel),
        "piEmail": labHead["mail"],
        "runDate": faker.date(),
        "runMode": "HiSeq High Output",
        "species": "Human",
        "platform": "Illumina",
        "barcodeId": "Innovation_Adapter 30",
        "genePanel": genePanel,
        "primaryId": "{}_{}".format(projectName, randint(1, 20)),
        "qcReports": [],
        "datasource": "igo",
        "dnaInputNg": None,
        "flowCellId": "{}".format(uuid.uuid4().hex[:8]),
        "importDate": "Not imported from SMILE",
        "readLength": "",
        "sampleName": sampleName,
        "sampleType": sampleType,
        "captureName": "{}-Tube{}".format(projectName, randint(1, 20)),
        "igoComplete": True,
        "labHeadName": labHead["name"],
        "sampleClass": sampleClass,
        "barcodeIndex": "AGTCAACA",
        "cmoInfoIgoId": libraryId,
        "cmoPatientId": patientName,
        "igoProjectId": projectName,
        "igoRequestId": projectName,
        "labHeadEmail": labHead["mail"],
        "libraryIgoId": libraryId,
        "oncotreeCode": oncoTreeCode,
        "preservation": preservation,
        "sampleOrigin": sampleOrigin,
        "cmoSampleName": sampleID,
        "flowCellLanes": [
            randint(2, 10)
        ],
        "libraryVolume": None,
        "oldSampleName": sampleID,
        "sampleAliases": [
            {
                "value": libraryId,
                "namespace": "igoId"
            },
            {
                "value": sampleName,
                "namespace": "investigatorId"
            }
        ],
        "smileSampleId": "Not imported from SMILE",
        "tumorOrNormal": T_Or_N_list[tumorOrNormal],
        "captureInputNg": str(randint(200, 400)),
        "cfDNA2dBarcode": None,
        "collectionYear": faker.year(),
        "patientAliases": [
            {
                "value": patientName,
                "namespace": "cmoId"
            }
        ],
        "qcAccessEmails": "",
        "smilePatientId": "Not imported from SMILE",
        "smileRequestId": "Not imported from SMILE",
        "tissueLocation": "",
        "dataAnalystName": dataAnalyst["name"],
        "dataAccessEmails": "",
        "dataAnalystEmail": dataAnalyst["mail"],
        "investigatorName": investigator["name"],
        "sequencingCenter": "MSKCC",
        "investigatorEmail": investigator["mail"],
        "otherContactEmails": "",
        "projectManagerName": "",
        "investigatorSampleId": sampleName,
        "captureConcentrationNm": str(uniform(1, 10)),
        "libraryConcentrationNgul": uniform(100, 150)
    }
    metadata_obj = FileMetadata(file=file, version=0, latest=True, metadata=file_metadata, user=user)
    return metadata_obj


def get_sample_info(faker, patient, num, sample_type, project):
    sample_name = "s_{}_{}_{}_{}".format(patient[2:], num, sample_type, project)
    sample_id = "{}_{}_{}".format(project, num, randint(1, 100))
    preservation = faker.preservation()
    sample_class = None
    sample_type = None
    sample_origin = None
    sample_type = None
    oncoTree_code = None
    if sample_type == 'N':
        sample_class = faker.normal_sample_class()
        sample_type = faker.normal_sample_type()
        sample_origin = faker.normal_sample_origin()
        oncoTree_code = faker.normal_onco_tree_code()
    else:
        sample_class = faker.tumor_sample_class()
        sample_type = faker.normal_sample_type()
        sample_origin = faker.tumor_sample_origin()
        oncoTree_code = faker.tumor_onco_tree_code()
    return (sample_name, sample_id, preservation, sample_class, sample_type, sample_origin, oncoTree_code)


def create_sample(faker, user, file_group, request, patient, sex, num_samples, pair_prob, genePanel, investigator, lab_head, data_analyst):
    file_type, _ = FileType.objects.get_or_create(name='fastq')
    count = 1
    sample_list = []
    metadata_list = []
    pair_percent = pair_prob * 100
    while count <= num_samples:
        for r in ['R1', 'R2']:
            sample_name, sample_id, preservation, sample_class, sample_type, sample_origin, oncoTree_code = get_sample_info(
                faker, patient, count, 'T', request)
            path = faker.file_path(depth=randint(3, 5), extension='fastq')
            file_name = os.path.basename(path)
            sample_file = File(file_name=file_name, path=path, file_type=file_type, file_group=file_group, size=0)
            sample_list.append(sample_file)
            metadata_list.append(create_sample_file_metadata(faker, sample_file, user, r, sample_id, sample_name, sample_class, sample_type, sample_origin,
                                                             sample_id, request, patient, sex, genePanel, oncoTree_code, preservation, investigator, lab_head, data_analyst, 0))
        if faker.boolean(chance_of_getting_true=pair_percent):
            for r in ['R1', 'R2']:
                sample_name, sample_id, preservation, sample_class, sample_type, sample_origin, oncoTree_code = get_sample_info(
                    faker, patient, count, 'N', request)
                path = faker.file_path(depth=randint(3, 5), extension='fastq')
                file_name = os.path.basename(path)
                sample_file = File(file_name=file_name, path=path, file_type=file_type, file_group=file_group, size=0)
                sample_list.append(sample_file)
                metadata_list.append(create_sample_file_metadata(faker, sample_file, user, r, sample_id, sample_name, sample_class, sample_type, sample_origin,
                                                                 sample_id, request, patient, sex, genePanel, oncoTree_code, preservation, investigator, lab_head, data_analyst, 1))
        count += 1
    return sample_list, metadata_list


def create_patient(faker, user, file_group, request, genePanel, investigator, lab_head, data_analyst, num_patients):
    count = 1
    patient_samples = []
    patient_metadata = []
    while count <= num_patients:
        num_normals = randint(2, 10)
        patient = 'C-{}'.format(uuid.uuid4().hex[:6])
        sex = faker.male_or_female()
        sample_list, metadata_list = create_sample(faker, user, file_group, request, patient, sex, num_normals,
                                                   uniform(0.75, 0.90), genePanel, investigator, lab_head, data_analyst)
        count += 1
        patient_samples.append(sample_list)
        patient_metadata.append(metadata_list)
    patient_samples = functools.reduce(operator.iconcat, patient_samples, [])
    patient_metadata = functools.reduce(operator.iconcat, patient_metadata, [])

    return patient_samples, patient_metadata


def get_assay_reference_metadata(data_type, assay):
    return {'genePanel': assay, 'data_type': data_type}


def get_reference_metadata(data_type):
    return {'data_type': data_type}


def get_pooled_normal_metadata(data_type, genePanel, preservation, primaryId):
    return {'data_type': data_type, 'primaryId': primaryId, 'genePanel': genePanel, 'preservation': preservation}


def get_output_metadata(data_type, assay, requestId, samples):
    return {'data_type': data_type, 'igoRequestId': requestId, 'genePanel': assay, 'samples': samples}


def get_datatype(name):
    return name.replace("{", " ").replace("}", " ").replace("_", " ").replace(".", " ").strip()


def create_reference_file(faker, user):
    files = REFERENCE_FILES
    file_group_name = "reference files"
    file_group = get_or_create_file_group(name=file_group_name)
    file_list = []
    file_metadata_list = []
    for single_file in files:
        file_ext = Path(single_file).suffix
        file_type, _ = FileType.objects.get_or_create(name=file_ext)
        data_type = get_datatype(single_file)
        metadata = get_reference_metadata(data_type)
        file_dir = faker.file_path(depth=3, extension='')
        file_path = os.path.join(file_dir, single_file)
        file = File(file_name=single_file, path=file_path, file_type=file_type, file_group=file_group, size=0)
        file_metadata = FileMetadata(file=file, version=0, latest=True, metadata=metadata, user=user)
        file_list.append(file)
        file_metadata_list.append(file_metadata)
    return file_list, file_metadata_list


def create_reference_assay_file(faker, user):
    file_list = []
    file_metadata_list = []
    for assay in RECIPES:
        file_template_list = ASSAY_REFERENCE_FILES
        file_group_name = "{}_references".format(assay)
        file_group = get_or_create_file_group(name=file_group_name)
        files = []
        for single_file in file_template_list:
            files.append(single_file.format(assay))
        for single_file in files:
            file_ext = Path(single_file).suffix
            file_type, _ = FileType.objects.get_or_create(name=file_ext)
            data_type = get_datatype(single_file)
            metadata = get_assay_reference_metadata(data_type, assay)
            file_dir = faker.file_path(depth=3, extension='')
            file_path = os.path.join(file_dir, single_file)
            file = File(file_name=single_file, path=file_path, file_type=file_type, file_group=file_group, size=0)
            file_metadata = FileMetadata(file=file, version=0, latest=True, metadata=metadata, user=user)
            file_list.append(file)
            file_metadata_list.append(file_metadata)
    return file_list, file_metadata_list


def create_pooled_normal_files(faker, user, preservation):
    file_template = "POOLEDNORMAL_{}.fastq"
    file_group = get_or_create_file_group(name=POOLED_NORMAL_GROUP_NAME)
    file_list = []
    file_metadata_list = []
    for assay in RECIPES:
        file_name = file_template.format(assay)
        file_ext = Path(file_name).suffix
        file_type, _ = FileType.objects.get_or_create(name=file_ext)
        data_type = get_datatype(file_name)
        primaryId = Path(file_name).stem
        metadata = get_pooled_normal_metadata(data_type, assay, preservation, primaryId)
        file_dir = faker.file_path(depth=3, extension='')
        file_path = os.path.join(file_dir, file_name)
        file = File(file_name=file_name, path=file_path, file_type=file_type, file_group=file_group, size=0)
        file_metadata = FileMetadata(file=file, version=0, latest=True, metadata=metadata, user=user)
        file_list.append(file)
        file_metadata_list.append(file_metadata)
    return file_list, file_metadata_list


def create_output_file(faker, user, output_template_list, name, requestId, assay, samples):
    file_template_list = output_template_list
    file_group_name = "Pipeline output"
    file_group = get_or_create_file_group(name=file_group_name)
    files = []
    for single_file in file_template_list:
        files.append(single_file.format(name))
    file_list = []
    file_metadata_list = []
    for single_file in files:
        file_ext = Path(single_file).suffix
        file_type, _ = FileType.objects.get_or_create(name=file_ext)
        data_type = get_datatype(single_file)
        metadata = get_output_metadata(data_type, assay, requestId, samples)
        file_dir = faker.file_path(depth=3, extension='')
        file_path = os.path.join(file_dir, single_file)
        file = File(file_name=single_file, path=file_path, file_type=file_type, file_group=file_group, size=0)
        file_metadata = FileMetadata(file=file, version=0, latest=True, metadata=metadata, user=user)
        file_list.append(file)
        file_metadata_list.append(file_metadata)
    return file_list, file_metadata_list


def create_all_reference_files(faker, user):
    file_1, metadata_1 = create_reference_file(faker, user)
    file_2, metadata_2 = create_reference_assay_file(faker, user)
    file_3, metadata_3 = create_pooled_normal_files(faker, user, 'FROZEN')
    files_list = [file_1, file_2, file_3]
    metadata_list = [metadata_1, metadata_2, metadata_3]
    metadata_list = functools.reduce(operator.iconcat, metadata_list, [])
    files_list = functools.reduce(operator.iconcat, files_list, [])
    File.objects.bulk_create(files_list)
    save_metadata(metadata_list)


def create_request(faker, num_requests, user):
    count = 1
    request_samples = []
    request_metadata = []
    while count <= num_requests:
        print("working on request: {}".format(count))
        genePanel = faker.recipe()
        request = "{}_{}{}".format(randint(10000, 99999), faker.uppercase_letter(), faker.uppercase_letter())
        file_group_name = "{}_fastqs".format(genePanel)
        file_group = get_or_create_file_group(name=file_group_name)
        investigator = faker.investigator()
        lab_head = faker.lab_head()
        data_analyst = faker.data_analyst()
        samples_list, metadata_list = create_patient(faker, user, file_group, request, genePanel,
                                                     investigator, lab_head, data_analyst, randint(1, 10))
        count += 1
        request_samples.append(samples_list)
        request_metadata.append(metadata_list)

    request_samples = functools.reduce(operator.iconcat, request_samples, [])
    request_metadata = functools.reduce(operator.iconcat, request_metadata, [])
    File.objects.bulk_create(request_samples)
    save_metadata(request_metadata)


def create_run_obj(faker, name, app, samples, status, tags, operator_run, job_group, start_date, end_date):
    output_directory = faker.file_path(depth=3, extension='')
    run = Run(name=name, app=app, status=status, output_directory=output_directory,
              tags=tags, operator_run=operator_run, job_group=job_group, notify_for_outputs=[])
    if not end_date:
        run_end_date = NOW
    else:
        run_end_date = end_date
    if status != RunStatus.CREATING:
        run.execution_id = str(uuid.uuid4())
        run_submit_date = faker.date_time_between_dates(
            datetime_start=start_date, datetime_end=run_end_date, tzinfo=EASTERN)
        run.submitted = run_submit_date
        if status != RunStatus.READY:
            run_start_date = run_submit_date + timedelta(minutes=randint(1, 120))
            run.started = run_start_date
            if status != RunStatus.RUNNING:
                run_end_date = run_start_date + timedelta(hours=randint(1, 100))
                run.finished_date = run_end_date
    run.save()
    run.samples.set(samples)
    return run


def save_metadata(metadata_list):
    for single_metadata in metadata_list:
        request_id = single_metadata.metadata.get(settings.REQUEST_ID_METADATA_KEY)
        sample_id = single_metadata.metadata.get(settings.SAMPLE_ID_METADATA_KEY)
        sample_name = single_metadata.metadata.get(settings.SAMPLE_NAME_METADATA_KEY)
        cmo_sample_name = single_metadata.metadata.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
        patient_id = single_metadata.metadata.get(settings.PATIENT_ID_METADATA_KEY)
        assay = single_metadata.metadata.get(settings.RECIPE_METADATA_KEY, "")
        investigator = single_metadata.metadata.get(settings.INVESTIGATOR_METADATA_KEY, "")
        pi = single_metadata.metadata.get(settings.LAB_HEAD_NAME_METADATA_KEY, "")
        if sample_id:
            sample, _ = Sample.objects.get_or_create(
                sample_id=sample_id, defaults={"cmo_sample_name": cmo_sample_name, "sample_name": sample_name}
            )

            single_metadata.file.sample = sample
            single_metadata.file.save(update_fields=("sample",))

        if request_id:
            request, _ = Request.objects.get_or_create(request_id=request_id)
            single_metadata.file.request = request
            single_metadata.file.save(update_fields=("request",))

        if patient_id:
            patient, _ = Patient.objects.get_or_create(patient_id=patient_id)
            single_metadata.file.patient = patient
            single_metadata.file.save(update_fields=("patient",))
        single_metadata.save()


def create_run_from_file(faker, user, first_file, second_file, status, operator_run, job_group, request_id, num, total, start_date, end_date):
    assay = first_file.metadata['genePanel']
    name = "{} run {} of {}".format(assay, num, total)
    lab_head_name = first_file.metadata['labHeadName']
    lab_head_email = first_file.metadata['labHeadEmail']
    sample_name_normal = first_file.metadata['primaryId']
    sample_name_tumor = second_file.metadata['primaryId']
    tags = {"assay": assay, 'labHeadName': lab_head_name, 'igoRequestId': request_id,
            'labHeadEmail': lab_head_email, 'sampleNameNormal': sample_name_normal, 'sampleNameTumor': sample_name_tumor}
    pipeline_list = list(Pipeline.objects.filter(name__regex=r'.*{}.*'.format(assay)))
    if not pipeline_list:
        pipeline = create_pipeline(faker, recipie=assay)
    else:
        pipeline = pipeline_list[0]
    app = pipeline
    samples = []
    for single_file in [first_file, second_file]:
        sample_id = single_file.metadata['primaryId']
        sample = Sample.objects.get(sample_id=sample_id)
        samples.append(sample)

    run = create_run_obj(faker, name, pipeline, samples, status, tags, operator_run, job_group, start_date, end_date)
    reference_files_group = get_or_create_file_group(name="reference files")
    assay_group_name = "{}_references".format(assay)
    assay_reference_files_group = get_or_create_file_group(name=assay_group_name)
    input_metadata = FileRepository.filter(file_group_in=[reference_files_group, assay_reference_files_group])
    for single_file_metadata in input_metadata:
        single_file = single_file_metadata.file
        port_obj = Port(run=run, name=single_file.file_name, port_type=PortType.INPUT)
        port_obj.save()
        port_obj.files.add(single_file)
    pair_name = "{}_{}".format(sample_name_normal, sample_name_tumor)
    if status == RunStatus.COMPLETED:
        file_1, metadata_1 = create_output_file(faker, user, PIPELINE_PAIR_OUTPUT_FILES, pair_name, request_id, assay, [
                                                sample_name_normal, sample_name_tumor])
        file_2, metadata_2 = create_output_file(
            faker, user, PIPELINE_SAMPLE_OUTPUT_FILES, sample_name_normal, request_id, assay, [sample_name_normal])
        file_3, metadata_3 = create_output_file(
            faker, user, PIPELINE_SAMPLE_OUTPUT_FILES, sample_name_tumor, request_id, assay, [sample_name_tumor])
        files_list = [file_1, file_2, file_3]
        metadata_list = [metadata_1, metadata_2, metadata_3]
        output_metadata_list = functools.reduce(operator.iconcat, metadata_list, [])
        output_files_list = functools.reduce(operator.iconcat, files_list, [])
        File.objects.bulk_create(output_files_list)
        save_metadata(output_metadata_list)
        for single_file in output_files_list:
            port_obj = Port(run=run, name=single_file.file_name, port_type=PortType.OUTPUT)
            port_obj.save()
            port_obj.files.add(single_file)


def get_pairs(request):
    files = FileRepository.filter(metadata={'igoRequestId': request, 'tumorOrNormal': T_Or_N_list[0]})
    pooled_normal_group = get_or_create_file_group(name=POOLED_NORMAL_GROUP_NAME)
    pairs = []
    for single_file in files:
        t_file = single_file
        t_sample_name = single_file.metadata["sampleName"]
        n_sample_name = t_sample_name.replace("_T_", "_N_")
        n_file_query = FileRepository.filter(metadata={'sampleName': n_sample_name})
        if n_file_query:
            n_file = n_file_query.first()
        else:
            assay = single_file.metadata['genePanel']
            pooled_normal_query = FileRepository.filter(
                file_group=pooled_normal_group, metadata={'genePanel': assay})
            if not pooled_normal_query:
                raise Exception("Pool normal for assay: {} not found".format(assay))
            else:
                n_file = pooled_normal_query.first()
        status = get_status()
        pairs.append((t_file, n_file, status))
    return pairs


def create_run_from_request(faker, user, num_requests):
    req_str = "igoRequestId"
    requests = list(FileRepository.filter(values_metadata=req_str, exclude={req_str: None}))
    current_request_num = 0
    while current_request_num < num_requests:
        print("working on run: {}".format(current_request_num))
        curr_request = sample(requests, 1)[0]
        pairs = get_pairs(curr_request)
        num_total = 0
        num_completed = 0
        num_failed = 0
        end_date = None
        for _, _, status in pairs:
            if status == RunStatus.ABORTED or status == RunStatus.FAILED:
                num_failed += 1
            if status == RunStatus.COMPLETED:
                num_completed += 1
            num_total += 1
        operator_status = RunStatus.RUNNING
        if num_failed > 0:
            operator_status = RunStatus.FAILED
            end_date = faker.date_time_between_dates(
                datetime_start=RUN_START, datetime_end=RUN_END, tzinfo=EASTERN)
        elif num_completed == num_total:
            operator_status = RunStatus.COMPLETED
            end_date = faker.date_time_between_dates(
                datetime_start=RUN_START, datetime_end=RUN_END, tzinfo=EASTERN)
        job_group = JobGroup()
        assay = pairs[0][0].metadata['genePanel']
        operator = create_new_operator(faker, recipie=assay)
        operator_run = OperatorRun(status=operator_status, operator=operator, num_total_runs=num_total,
                                   num_completed_runs=num_completed, num_failed_runs=num_failed, job_group=job_group, finished_date=end_date)
        job_group.save()
        operator_run.save()
        count = 0
        for single_pair in pairs:
            status = single_pair[2]
            if status != RunStatus.COMPLETED and status != RunStatus.FAILED and status != RunStatus.ABORTED:
                start_date = NOW - timedelta(hours=randint(1, 120))
                end_date = None
            else:
                if not end_date:
                    start_date = NOW - timedelta(hours=randint(1, 120))
                    end_date = start_date + timedelta(hours=randint(1, 60))
                else:
                    start_date = end_date - timedelta(hours=randint(1, 120))
            create_run_from_file(faker, user, single_pair[0], single_pair[1], single_pair[2], operator_run,
                                 job_group, curr_request, count, len(pairs), start_date, end_date)
            count += 1
        current_request_num += 1


def run(*args):
    faker = set_up_faker()
    user = create_user()
    runs_req = re.compile(r'runs=\d+')
    requests_req = re.compile(r'requests=\d+')
    num_req = re.compile(r'\d+')
    request_param_list = list(filter(requests_req.match, list(args)))
    run_param_list = list(filter(runs_req.match, list(args)))
    if not request_param_list:
        print("Please specify the number of requests. Example: requests=300")
    if not run_param_list:
        print("Please specify the number of runs. Example: runs=100")
    request_param = int(num_req.findall(request_param_list[0])[0])
    create_request(faker, request_param, user)
    run_param = int(num_req.findall(run_param_list[0])[0])
    create_all_reference_files(faker, user)
    create_run_from_request(faker, user, run_param)
