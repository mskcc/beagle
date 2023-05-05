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

FIXTURES = [
    "runner/tests/operator/access/v2_1_0/manifest/0a3c70a9-cf89-466b-bd39-4f409c21fb41.files.json",
    "runner/tests/operator/access/v2_1_0/manifest/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.input.json",
    "runner/tests/operator/access/v2_1_0/manifest/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.output.json",
    "runner/tests/operator/access/v2_1_0/manifest/0a3c70a9-cf89-466b-bd39-4f409c21fb41.run.json",
    "runner/tests/operator/access/v2_1_0/manifest/0a3c70a9-cf89-466b-bd39-4f409c21fb41.samples.json",
]

COMMON_FIXTURES = [
    "runner/fixtures/runner.pipeline.json",
    "runner/fixtures/runner.operator_run.json",
    "file_system/fixtures/file_system.filegroup.json",
    "file_system/fixtures/file_system.filetype.json",
    "file_system/fixtures/file_system.storage.json",
    "beagle_etl/fixtures/beagle_etl.operator.json",
    "file_system/fixtures/DMP_data.json"
]


class TestAcessManifestOperator(TestCase):
    fixtures = [os.path.join(ROOT_DIR, f) for f in FIXTURES + COMMON_FIXTURES]
    expected_csv_content = 'igoRequestId,primaryId,cmoPatientId,dmpPatientId,dmpImpactSamples,dmpAccessSamples,baitSet,libraryVolume,investigatorSampleId,preservation,species,libraryConcentrationNgul,tissueLocation,sampleClass,sex,cfDNA2dBarcode,sampleOrigin,tubeId,tumorOrNormal,captureConcentrationNm,oncotreeCode,dnaInputNg,collectionYear,captureInputNg\n12345_A,12345_A_25,C-ALLANT,P-0000001,P-0000002-T01-IM6;P-0000001-T01-IM6,,null,0,A-000000,,,0,,,F,,Whole Blood,,Tumor,0,,0,,0\n""\n'
    file_path_pattern = "/tmp/12345_A/*/manifest.csv"
    def test_access_manifest_operator(self):
        """
        Test Access manifest operator
        """
        settings.BEAGLE_SHARED_TMPDIR = "/tmp"
        # Check Operator basics
        request_id = "12345_A"
        operator_model = Operator.objects.get(id=20)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        operator.OUTPUT_DIR = "/tmp" # overide directory defaults for testing 
        self.assertEqual(operator.get_pipeline_id(), "0d6c2863-52a2-4c5b-ad1b-8664ee74b7b7")
        self.assertEqual(str(operator.model), "AccessManifestOperator_2_1_0")
        self.assertEqual(operator.request_id, request_id)
        self.assertEqual(operator._jobs, [])
        # Get Jobs
        jobs = operator.get_jobs()
        self.assertEqual(len(jobs) > 0, True)
        # Check if the file exists, use glob since we are unsure of what the date will be 
        file = glob.glob(self.file_path_pattern)
        self.assertEqual(len(file) == 1, True)
        file_name = file[0]
        # Check contents
        with open(file_name, 'r') as file:
            csv_string = file.read()
        self.assertEqual(csv_string, self.expected_csv_content)
        # Check if file can be queried
        file_query = File.objects.filter(file_group__slug="access_manifests", path=file_name)
        # Check Query data 
        self.assertEqual(len(file_query) == 1, True)
        file_query_object = file_query[0]
        self.assertEqual(file_query_object.path, file_name)

    def tearDown(self):
        # clean up tmp directory
        shutil.rmtree('/tmp/12345_A')

