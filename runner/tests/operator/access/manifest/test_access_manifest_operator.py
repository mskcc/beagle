import os

from django.test import TestCase

from beagle import settings
from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata
from runner.operator.operator_factory import OperatorFactory
import datetime
import glob
import shutil

# general fixtures
COMMON_FIXTURES = [
    "runner/fixtures/runner.pipeline.json",
    "runner/fixtures/runner.operator_run.json",
    "file_system/fixtures/file_system.filegroup.json",
    "file_system/fixtures/file_system.filetype.json",
    "file_system/fixtures/file_system.storage.json",
    "beagle_etl/fixtures/beagle_etl.operator.json",
    "file_system/fixtures/DMP_data.json",
    "runner/fixtures/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.samples.json",
    "runner/fixtures/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.files.json",
    "runner/fixtures/4d9c8213-df56-4a0f-8d86-ce2bd8349c59.samples.json",
    "runner/fixtures/4d9c8213-df56-4a0f-8d86-ce2bd8349c59.files.json",
    "file_system/fixtures/13893_B.file.json",
    "file_system/fixtures/13893_B.filemetadata.json",
]


class TestAcessManifestOperator(TestCase):
    # test db
    fixtures = [os.path.join(ROOT_DIR, f) for f in COMMON_FIXTURES]
    # variables to help check operator output
    expected_csv_content = [
        'igoRequestId,primaryId,cmoPatientId,dmpPatientId,dmpImpactSamples,dmpAccessSamples,baitSet,libraryVolume,investigatorSampleId,preservation,species,libraryConcentrationNgul,tissueLocation,sampleClass,sex,cfDNA2dBarcode,sampleOrigin,tubeId,tumorOrNormal,captureConcentrationNm,oncotreeCode,dnaInputNg,collectionYear,captureInputNg\n13893_B,13893_B_1,ALLANT2,P-0000002,P-0000005-T01-IM6;P-0000004-T01-IM6,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-1234567-N00-XS1,EDTA-Streck,,69.0,,Blood,M,8042889270,Whole Blood,,Normal,14.49275362,,200.0,,999.99999978\n13893_B,13893_B_3,ALLANT,P-0000001,P-0000002-T01-IM6;P-0000001-T01-IM6,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-1234567-N00-XS1,EDTA-Streck,,102.5,,Blood,M,8042889270,Whole Blood,,Normal,9.756097561,,200.0,,1000.0000000025001\n13893_B,13893_B_2,ALLANT3,,,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-1234567-N00-XS1,EDTA-Streck,,74.5,,Blood,M,8042889270,Whole Blood,,Normal,13.42281879,,200.0,,999.999999855\n""\n'
    ]

    def test_access_manifest_operator(self):
        """
        Test access manifest operator
        """
        settings.BEAGLE_SHARED_TMPDIR = "/tmp"
        # Check Operator basics
        request_id = "13893_B"
        operator_model = Operator.objects.get(id=20)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "0d6c2863-52a2-4c5b-ad1b-8664ee74b7b7")
        self.assertEqual(str(operator.model), "AccessManifestOperator_2_1_0")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])
        # Get Jobs
        jobs = operator.get_jobs()
        self.assertEqual(len(jobs) > 0, True)
        for i, job in enumerate(jobs):
            # check job json is correct
            self.assertEqual(job.is_valid(), True)
            input_json = job.inputs
            self.assertEqual(len(input_json["manifest_data"]), 2)
            # Check contents
            manifest_path = input_json["manifest_data"]["location"].replace("juno:", "")
            with open(manifest_path, "r") as file:
                csv_string = file.read()
            self.assertEqual(csv_string, self.expected_csv_content[i])
