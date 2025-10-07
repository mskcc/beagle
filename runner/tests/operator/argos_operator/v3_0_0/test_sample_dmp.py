import json
import os
from datetime import datetime
from pprint import pprint
from uuid import UUID

from django.conf import settings
from django.core.management import call_command
from django.db.models import Prefetch, Q
from django.test import TestCase, override_settings

from file_system.models import File, FileGroup, FileMetadata, FileType
from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.v3_0_0.bin.sample_igo import SampleIGO
from runner.operator.argos_operator.v3_0_0.utils.barcode_utils import \
    spoof_barcode
from runner.operator.argos_operator.v3_0_0.utils.sample_utils import \
    get_samples_dmp


class TestSampleDMP(TestCase):
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

    def test_create_sample_clinical_bams(self):
        from pprint import pprint

        # get example tumors
        files = FileRepository.filter(queryset=self.files, metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})

        samples = {}
        file_list = {}

        for f in files:
            sample_name = f.metadata["ciTag"]
            file_list.setdefault(sample_name, []).append(f)

        for sample_name in file_list:
            sample_igo = SampleIGO(sample_name, file_list[sample_name], "fastq")
            samples[sample_name] = sample_igo

        samples_tumor = [samples["s_C_MP76JR_X001_d"], samples["s_C_4LM16H_X001_d"]]

        # get dmp bam for matching tumor
        for sample_tumor in samples_tumor:
            metadata = sample_tumor.metadata
            dmp_sample = get_samples_dmp(metadata)
            pprint(dmp_sample.dmp_bam_normal)
