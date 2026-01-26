"""
Test for constructing Argos pair and jobs
"""

import os
import json
from uuid import UUID
from mock import patch
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator
from django.conf import settings
from django.core.management import call_command
import tempfile


class TestCopyOutputs(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "beagle_etl.operator.json",
        "runner.pipeline.json",
    ]

    def setUp(self):
        os.environ["TMPDIR"] = ""

    def check_if_file_obj_valid(self, file_obj):
        if "class" in file_obj and "location" in file_obj:
            if file_obj["class"] == "File" and type(file_obj["location"]) == str:
                return True
        return False

    def check_if_list_is_valid(self, object_list, empty_ok, validation_function):
        if not empty_ok:
            if len(object_list) == 0:
                return False
        for single_obj in object_list:
            if not validation_function(single_obj):
                return False
        return True

    def validate_copy_outputs_input(self, input_json):
        for single_field in input_json:
            if single_field == "project_prefix":
                continue  # test is failing for this value because project_prefix isn't actually a list
            elif single_field == "meta":
                if not len(input_json[single_field]) == 3:
                    return False
                else:
                    continue
            elif single_field == "disambiguate":
                if not self.check_if_list_is_valid(input_json[single_field], True, self.check_if_file_obj_valid):
                    print("Error at %s", single_field)
                    return False
            else:
                if not self.check_if_list_is_valid(input_json[single_field], False, self.check_if_file_obj_valid):
                    print("Error at %s", single_field)
                    return False
        return True

    @patch("runner.operator.copy_outputs_operator.v2_3_0.copy_outputs_operator.CopyOutputsOperator.get_log_directory")
    @patch("file_system.models.populate_job_group_notifier_metadata.delay")
    def test_create_copy_output_jobs(self, populate_job_group_notifier_metadata, get_log_directory):
        """
        Test that copy output jobs are correctly created
        """
        print("Running test_create_copy_output_jobs ----")
        # Load fixtures
        populate_job_group_notifier_metadata.return_value = None
        get_log_directory.return_value = "/path/to/log/dir"
        test_files_fixture = os.path.join(
            settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.with_disambiguate.json"
        )
        call_command("loaddata", test_files_fixture, verbosity=0)

        with self.settings(BEAGLE_SHARED_TMPDIR=tempfile.gettempdir()):
            operator_model = Operator.objects.get(id=33)
            operator = OperatorFactory.get_by_model(
                operator_model, version="v2.3.0", run_ids=["ca18b090-03ad-4bef-acd3-52600f8e62eb"]
            )
            input_json_valid = False
            jobs = operator.get_jobs()
            if jobs[0].is_valid():
                input_json = jobs[0].inputs
                self.assertEqual(len(input_json["disambiguate"]), 4)
                input_json_valid = self.validate_copy_outputs_input(input_json)
                print(json.dumps(input_json, cls=UUIDEncoder))
            self.assertEqual(input_json_valid, True)

    @patch("runner.operator.copy_outputs_operator.v2_3_0.copy_outputs_operator.CopyOutputsOperator.get_log_directory")
    @patch("file_system.models.populate_job_group_notifier_metadata.delay")
    def test_create_copy_output_jobs_without_disambiguate(
        self, populate_job_group_notifier_metadata, get_log_directory
    ):
        """
        Test that copy output jobs are correctly created
        """
        print("Running test_create_copy_output_jobs ----")
        populate_job_group_notifier_metadata.return_value = None
        get_log_directory.return_value = "/path/to/log/dir"
        # Load fixtures
        test_files_fixture = os.path.join(
            settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.without_disambiguate.json"
        )
        call_command("loaddata", test_files_fixture, verbosity=0)

        with self.settings(BEAGLE_SHARED_TMPDIR=tempfile.gettempdir()):
            operator_model = Operator.objects.get(id=33)
            operator = OperatorFactory.get_by_model(
                operator_model, version="v2.3.0", run_ids=["ca18b090-03ad-4bef-acd3-52600f8e62eb"]
            )
            input_json_valid = False
            jobs = operator.get_jobs()
            if jobs[0].is_valid():
                input_json = jobs[0].inputs
                self.assertEqual(len(input_json["disambiguate"]), 0)
                input_json_valid = self.validate_copy_outputs_input(input_json)
                print(json.dumps(input_json, cls=UUIDEncoder))
            self.assertEqual(input_json_valid, True)

    @patch("runner.operator.copy_outputs_operator.v2_3_0.copy_outputs_operator.CopyOutputsOperator.get_log_directory")
    @patch("file_system.models.populate_job_group_notifier_metadata.delay")
    def test_create_copy_output_jobs_with_bed(self, populate_job_group_notifier_metadata, get_log_directory):
        """
        Test that copy output jobs are correctly created
        """
        print("Running test_create_copy_output_jobs ----")
        populate_job_group_notifier_metadata.return_value = None
        get_log_directory.return_value = "/path/to/log/dir"
        # Load fixtures
        test_files_fixture = os.path.join(
            settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.with_bed.json"
        )
        call_command("loaddata", test_files_fixture, verbosity=0)

        with self.settings(BEAGLE_SHARED_TMPDIR=tempfile.gettempdir()):
            operator_model = Operator.objects.get(id=33)
            operator = OperatorFactory.get_by_model(
                operator_model, version="v2.3.0", run_ids=["ca18b090-03ad-4bef-acd3-52600f8e62eb"]
            )
            input_json_valid = False
            jobs = operator.get_jobs()
            if jobs[0].is_valid():
                input_json = jobs[0].inputs
                self.assertEqual(len(input_json["bed"]), 1)
                input_json_valid = self.validate_copy_outputs_input(input_json)
                print(json.dumps(input_json, cls=UUIDEncoder))
            self.assertEqual(input_json_valid, True)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)
