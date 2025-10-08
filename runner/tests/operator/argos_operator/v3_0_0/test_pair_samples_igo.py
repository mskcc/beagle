import csv
import os
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from file_system.models import File, FileGroup, FileMetadata, FileType
from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.v3_0_0.bin.sample_igo import SampleIGO
from runner.operator.argos_operator.v3_0_0.utils.sample_utils import \
    pair_samples_igo
from runner.run.processors.file_processor import FileProcessor

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
PROJECT_ROOT = SCRIPT_DIR / "operator" / "argos_operator" / "v3_0_0"
CSV_PATH = PROJECT_ROOT / "assets" / "pooled_normals.csv"
POOLED_NORMALS = {}

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_ID_METADATA_KEY,  # primaryId
    settings.PATIENT_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.CMO_SAMPLE_TAG_METADATA_KEY,  # ciTag
    settings.LIBRARY_ID_METADATA_KEY,
    settings.BAITSET_METADATA_KEY,
    settings.PRESERVATION_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
    "runMode",
    "runId",
]


# Taken from sample_pooled_normal.py
def load_csv_to_global_dict(filepath):
    global POOLED_NORMALS  # contains table from assets/pooled_normals.csv
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_name = "_".join([row["bait_set"], row["preservation_type"], row["machine"], "POOLED_NORMAL"])
            sample_name = sample_name.upper()
            POOLED_NORMALS[sample_name] = row
            POOLED_NORMALS[sample_name]["pooled_normals_paths"] = (
                POOLED_NORMALS[sample_name]["pooled_normals_paths"].strip("{}").split(",")
            )


class TestPairSamplesIGO(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "DMP_data.json",
    ]

    def setUp(self):
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
            call_command("loaddata", "DMP_data.json")
            test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "argos_v3_0_0.meta.json")
            call_command("loaddata", test_files_fixture, verbosity=0)
        except Exception as e:
            print(f"Error in setUp: {e}")

        self.files = FileRepository.all()

        load_csv_to_global_dict(CSV_PATH)

        # need to add file paths to test db
        for sample_name in POOLED_NORMALS:
            d = POOLED_NORMALS[sample_name]
            paths = d["pooled_normals_paths"]

            metadata = dict()
            metadata["baitSet"] = d["bait_set"]
            metadata["genePanel"] = d["gene_panel"]
            metadata["machine"] = d["machine"]
            metadata["preservation"] = d["preservation_type"]
            for path in paths:
                FileProcessor.create_file_obj("file://" + path, 0, "12345", "b6857a56-5d45-451f-b4f6-26148946080f", d)

        # create fake dmp bams for the patients above
        for sample_tumor in ("C-MP76JR", "C-4LM16H"):
            fname = sample_tumor + ".bam"
            fname_bai = sample_tumor + ".bai"
            patient_cmo = sample_tumor.replace("C-", "")
            pname = "/" + fname
            metadata = {
                "bai": fname_bai,
                "bam": fname,
                "type": "N",
                "assay": "IM7",
                "sample": "P-1234567-N01-IM6",
                "anon_id": "anon-" + patient_cmo + "-N",
                "patient": {
                    "cmo": patient_cmo,
                    "dmp": "P-1234567",
                    "updated": "2020-03-19T23:57:51.941963Z",
                    "imported": "2020-03-19T23:57:51.941945Z",
                },
                "updated": "2020-03-25T19:45:16.421154Z",
                "version": 1,
                "coverage": 648,
                "imported": "2020-03-25T19:45:16.421137Z",
                "cmo_assay": "IMPACT505",
                "tumor_type": "MBC",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "external_id": "s_" + patient_cmo.lower().replace("-", "_") + "_N901_dZ_IM6",
                "sample_type": "0",
                "tissue_type": "Breast",
                "primary_site": "Breast",
                "project_name": "UK12344567890VB",
                "patient_group": "Group_12344567890",
                "part_c_consent": 1,
                "metastasis_site": "Not Applicable",
                "somatic_calling_status": "Matched",
                "major_allele_contamination": 0.452,
                "minor_allele_contamination": 0.00069,
            }
            file_group_instance = FileGroup.objects.get(name="DMP BAMs")
            filetype_instance = FileType.objects.get(name="bam")
            file_instance = File.objects.create(
                file_type=filetype_instance, file_group=file_group_instance, file_name=fname, path=pname
            )
            FileMetadata.objects.create_or_update(file=file_instance, version=1, metadata=metadata)

    def test_create_pairs(self):
        files = FileRepository.filter(queryset=self.files, metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})

        samples = dict()
        file_list = dict()
        for f in files:
            sample_name = f.metadata["ciTag"]
            file_list.setdefault(sample_name, []).append(f)

        for sample_name in file_list:
            sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")
            samples[sample_name] = sample_igo

        # TODO check samples are built properly
        self.assertEqual(len(file_list), 4)

        samples_tumor = [samples["s_C_MP76JR_X001_d"], samples["s_C_4LM16H_X001_d"]]

        best, full = pair_samples_igo(samples_tumor)

        for sample in samples_tumor:
            print(sample.sample_name + " ---")
            print("Print all pairs for each tumor")
            print(full[sample.sample_name].generate_pairing())
            print()
            print("Print just the best pair per tumor")
            print(best[sample.sample_name].generate_pairing())
