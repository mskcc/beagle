import os
import json

from django.test import TestCase

from beagle.settings import ROOT_DIR
from beagle_etl.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.operator.access.v1_0_0.sample_sheet import AccessSampleSheetOperator


COMMON_FIXTURES = [
    'fixtures/tests/10075_D_single_TN_pair.file.json',
    'fixtures/tests/10075_D_single_TN_pair.filemetadata.json',
    'runner/fixtures/runner.pipeline.json',
    'runner/fixtures/runner.run.json',
    'runner/fixtures/runner.operator_run.json',
    'file_system/fixtures/file_system.filegroup.json',
    'file_system/fixtures/file_system.filetype.json',
    'file_system/fixtures/file_system.storage.json',
    'beagle_etl/fixtures/beagle_etl.operator.json',
]


class TestSampleSheeetOperator(TestCase):

    fixtures = [os.path.join(ROOT_DIR, f) for f in COMMON_FIXTURES]

    def test_sample_sheet_operator(self):
        request_id = "10075_D"
        operator_model = Operator.objects.get(slug="AccessSampleSheetOperator")
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_jobs()[0][0].is_valid(), True)
        input_json = operator.get_jobs()[0][0].initial_data['inputs']
        print(json.dumps(input_json))
        self.assertEqual(input_json, {"samples": [{"lane": 3, "sample_id": "10075_D_5",
                                                   "sample_plate": "Tumor", "sample_well":
                                                   "IMPACT468", "17_index_id":
                                                   "DUAL_IDT_LIB_267", "index": "GTATTGGC",
                                                   "index2": "TTGTCGGT", "sample_project":
                                                   "Project_10075_D", "description": ""},
                                                  {"lane": 4, "sample_id": "10075_D_5",
                                                   "sample_plate": "Tumor", "sample_well":
                                                   "IMPACT468", "17_index_id":
                                                   "DUAL_IDT_LIB_267", "index": "GTATTGGC",
                                                   "index2": "TTGTCGGT", "sample_project":
                                                   "Project_10075_D", "description": ""},
                                                  {"lane": 3, "sample_id": "10075_D_5",
                                                   "sample_plate": "Tumor", "sample_well":
                                                   "IMPACT468", "17_index_id":
                                                   "DUAL_IDT_LIB_267", "index": "GTATTGGC",
                                                   "index2": "TTGTCGGT", "sample_project":
                                                   "Project_10075_D", "description": ""},
                                                  {"lane": 4, "sample_id": "10075_D_5",
                                                   "sample_plate": "Tumor", "sample_well":
                                                   "IMPACT468", "17_index_id":
                                                   "DUAL_IDT_LIB_267", "index": "GTATTGGC",
                                                   "index2": "TTGTCGGT", "sample_project":
                                                   "Project_10075_D", "description": ""},
                                                  {"lane": 1, "sample_id": "10075_D_3",
                                                   "sample_plate": "Normal", "sample_well":
                                                   "IMPACT468", "17_index_id": None, "index":
                                                   "GTATTGGC", "index2": "TTGTCGGT",
                                                   "sample_project": "Project_10075_D",
                                                   "description": ""}, {"lane": 2, "sample_id":
                                                                        "10075_D_3",
                                                                        "sample_plate":
                                                                        "Normal", "sample_well":
                                                                        "IMPACT468",
                                                                        "17_index_id": None,
                                                                        "index": "GTATTGGC",
                                                                        "index2": "TTGTCGGT",
                                                                        "sample_project":
                                                                        "Project_10075_D",
                                                                        "description": ""},
                                                  {"lane": 3, "sample_id": "10075_D_3",
                                                   "sample_plate": "Normal", "sample_well":
                                                   "IMPACT468", "17_index_id": None, "index":
                                                   "GTATTGGC", "index2": "TTGTCGGT",
                                                   "sample_project": "Project_10075_D",
                                                   "description": ""}, {"lane": 1, "sample_id":
                                                                        "10075_D_3",
                                                                        "sample_plate":
                                                                        "Normal", "sample_well":
                                                                        "IMPACT468",
                                                                        "17_index_id": None,
                                                                        "index": "GTATTGGC",
                                                                        "index2": "TTGTCGGT",
                                                                        "sample_project":
                                                                        "Project_10075_D",
                                                                        "description": ""},
                                                  {"lane": 2, "sample_id": "10075_D_3",
                                                   "sample_plate": "Normal", "sample_well":
                                                   "IMPACT468", "17_index_id": None, "index":
                                                   "GTATTGGC", "index2": "TTGTCGGT",
                                                   "sample_project": "Project_10075_D",
                                                   "description": ""}, {"lane": 3, "sample_id":
                                                                        "10075_D_3",
                                                                        "sample_plate":
                                                                        "Normal", "sample_well":
                                                                        "IMPACT468",
                                                                        "17_index_id": None,
                                                                        "index": "GTATTGGC",
                                                                        "index2": "TTGTCGGT",
                                                                        "sample_project":
                                                                        "Project_10075_D",
                                                                        "description": ""}]})
