from urllib import request
from notifier.models import Notifier
from beagle_etl.models import Operator
from runner.models import Run, RunStatus, OperatorRun, TriggerAggregateConditionType, TriggerRunType, Pipeline
from django.contrib.auth.models import User
from notifier.models import Notifier
from file_system.models import FileGroup, File, FileMetadata, FileType
from random import randint, sample, uniform
from coolname import generate, generate_slug
from faker import Faker
from faker.providers import DynamicProvider
import uuid
import os
import string
from celery import current_app as app
import functools
import operator
import re

NUM_INVESTIGATOR = 30
NUM_LAB_HEAD = 30
NUM_DATA_ANALYST = 30

app.conf.task_always_eager = True

RECIPES = ["IMPACT505", "ACCESS", "CMO-CH", "HumanWholeGenome", "ShallowWGS", "WholeExomeSequencing"]
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
T_Or_N_list = ["Tumor", "Normal"]


def set_up_faker():
    Faker.seed(0)
    fake = Faker()
    INVESTIGATOR_LIST = [fake.simple_profile() for _ in range(NUM_INVESTIGATOR)]
    LAB_HEAD_LIST = [fake.simple_profile() for _ in range(NUM_LAB_HEAD)]
    DATA_ANALYST_LIST = [fake.simple_profile() for _ in range(NUM_DATA_ANALYST)]
    UPPERCASE_LETTERS = string.ascii_letters.upper()
    fake_recipes = DynamicProvider(provider_name="recipes", elements=RECIPES)
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
    fake.add_provider(fake_recipes)
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


def create_multiple_objects(object_number, object_method, **method_kwargs):
    object_count = 0
    while object_count < object_number:
        object_method(method_kwargs)
        object_count += 1


def create_file_group(name=None):
    if not name:
        name = generate_slug()
    new_file_group, _ = FileGroup.objects.get_or_create(name=name)
    return new_file_group


def create_notifier(faker):
    default = faker.boolean()  # sample(TRUE_OR_FALSE, 1)[0]
    notifier_type = faker.notifier_type()
    board = "ALL"
    if notifier_type != "EMAIL":
        board = generate_slug(2)
    new_notifier = Notifier(default=default, notifier_type=notifier_type, board=board)
    new_notifier.save()
    return new_notifier


def create_new_operator():
    slug = generate_slug()
    class_name = "runner.operator.{}".format(generate_slug(2))
    version = "{}.{}.{}".format(randint(0, 9), randint(0, 9), randint(0, 9))
    all_recipe = [",".join(recipes)]
    recipe_list = recipes + all_recipe
    recipes = sample(recipe_list, 1)[0]
    notifier = create_notifier()
    new_operator = Operator(slug=slug, class_name=class_name, version=version, recipes=recipes, notifier=notifier)
    new_operator.save()
    return new_operator


def create_pipeline(faker):
    #current_names = list(Pipeline.objects.values_list("name",flat=True).distinct())
    name = generate(3)
    github = "https://github.com/mskcc/mock_pipeline"
    version = "{}.{}.{}".format(randint(0, 9), randint(0, 9), randint(0, 9))
    entrypoint = faker.file_name(extension='cwl')
    output_file_group = create_file_group()
    new_operator = create_new_operator()
    default = faker.boolean()
    walltime = randint(1, 1000)
    memlimit = "{]gb".format(randint(1, 100))
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
    while count <= num_samples:
        for r in ['R1', 'R2']:
            sample_name, sample_id, preservation, sample_class, sample_type, sample_origin, oncoTree_code = get_sample_info(
                faker, patient, count, 'N', request)
            path = faker.file_path(depth=randint(3, 5), extension='fastq')
            file_name = os.path.basename(path)
            sample_file = File(file_name=file_name, path=path, file_type=file_type, file_group=file_group, size=0)
            sample_list.append(sample_file)
            metadata_list.append(create_sample_file_metadata(faker, sample_file, user, r, sample_id, sample_name, sample_class, sample_type, sample_origin,
                                                             sample_id, request, patient, sex, genePanel, oncoTree_code, preservation, investigator, lab_head, data_analyst, 1))
        if faker.boolean(chance_of_getting_true=pair_prob):
            for r in ['R1', 'R2']:
                sample_name, sample_id, preservation, sample_class, sample_type, sample_origin, oncoTree_code = get_sample_info(
                    faker, patient, count, 'T', request)
                path = faker.file_path(depth=randint(3, 5), extension='fastq')
                file_name = os.path.basename(path)
                sample_file = File(file_name=file_name, path=path, file_type=file_type, file_group=file_group, size=0)
                sample_list.append(sample_file)
                metadata_list.append(create_sample_file_metadata(faker, sample_file, user, r, sample_id, sample_name, sample_class, sample_type, sample_origin,
                                                                 sample_id, request, patient, sex, genePanel, oncoTree_code, preservation, investigator, lab_head, data_analyst, 0))
        count += 1
    return sample_list, metadata_list


def create_patient(faker, user, file_group, request, genePanel, investigator, lab_head, data_analyst, num_patients):
    count = 1
    patient_samples = []
    patient_metadata = []
    while count <= num_patients:
        num_normals = randint(5, 20)
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


def create_request(faker, num_requests, user):
    count = 1
    request_samples = []
    request_metadata = []
    while count <= num_requests:
        print("working on request: {}".format(count))
        genePanel = faker.recipes()
        request = "{}_{}{}".format(randint(10000, 99999), faker.uppercase_letter(), faker.uppercase_letter())
        file_group_name = "{}_fastqs".format(genePanel)
        file_group = create_file_group(name=file_group_name)
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
    FileMetadata.objects.bulk_create(request_metadata)


def run(*args):
    faker = set_up_faker()
    user = create_user()
    requests_req = re.compile(r'requests=\d+')
    num_req = re.compile(r'\d+')
    request_param_list = list(filter(requests_req.match, list(args)))
    if not request_param_list:
        print("Please specify the number of requests. Example: requests=300")
    request_param = int(num_req.findall(request_param_list[0])[0])
    create_request(faker, request_param, user)
