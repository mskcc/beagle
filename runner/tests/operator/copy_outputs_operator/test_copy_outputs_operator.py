"""
Test for constructing Roslin pair and jobs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata, FileGroup, FileType
from django.conf import settings
from django.core.management import call_command

class TestCopyOutputs(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "beagle_etl.operator.json",
    "runner.pipeline.json"
    ]

    def setUp(self):
        os.environ['TMPDIR'] = ''

    def check_if_file_obj_valid(self,file_obj):
        if 'class' in file_obj and 'path' in file_obj:
            if file_obj['class'] == 'File' and type(file_obj['path']) == str:
                return True
        return False

    def check_if_list_is_valid(self,object_list, empty_ok,validation_function):
        if not empty_ok:
            if len(object_list) == 0:
                return False
        for single_obj in object_list:
            if not validation_function(single_obj):
                return False
        return True

    def check_if_pair_record_is_valid(self,record):
        if 'normal_id' not in record or 'tumor_id' not in record or 'files' not in record:
            return False
        if not record['files']:
            return False
        else:
            return self.check_if_list_is_valid(record['files'],False,self.check_if_file_obj_valid)




    def validate_copy_outputs_input(self,input_json):
        for single_field in input_json:
            if single_field != 'facets':
                if not self.check_if_list_is_valid(input_json[single_field],False,self.check_if_file_obj_valid):
                    return False
            else:
                if not self.check_if_list_is_valid(input_json[single_field],False,self.check_if_pair_record_is_valid):
                    return False
        return True


    def test_create_copy_output_jobs(self):
        """
        Test that Roslin jobs are correctly created
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        operator_model = Operator.objects.get(id=4)
        operator = OperatorFactory.get_by_model(operator_model,  run_ids=["ca18b090-03ad-4bef-acd3-52600f8e62eb"])
        input_json_valid = False
        if operator.get_jobs()[0].is_valid():
            input_json = operator.get_jobs()[0].initial_data['inputs']
            input_json_valid = self.validate_copy_outputs_input(input_json)
        self.assertEqual(input_json_valid,True)

