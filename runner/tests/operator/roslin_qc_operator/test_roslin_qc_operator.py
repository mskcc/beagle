"""
Tests for Roslin QC Operator class
"""
import os
import json
from mock import patch
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from runner.operator.roslin_qc_operator.roslin_qc_operator import RoslinQcOperator
from django.conf import settings
from django.core.management import call_command
from runner.models import Pipeline, Run
from runner.tasks import create_run_task

class TestRoslinQcOperator(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json"
    ]

    def test_operator_factory_roslin_qc1(self):
        """
        Test that a Roslin QC operator instance can be created with Operator.factory
        """
        pipeline_type = "roslin-qc"
        request_id = "foo"
        operator = OperatorFactory.factory(pipeline_type, request_id)
        self.assertTrue(isinstance(operator, RoslinQcOperator))
        self.assertTrue( operator.pipeline_id == "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a")
        self.assertTrue( operator.operator == "roslin-qc")
        self.assertTrue( operator.request_id == "foo")
        self.assertTrue( operator._jobs == [])
        self.assertTrue( len(operator.files) == 0)

    def test_operator_factory_get_by_class_name(self):
        """
        Test that you can get the RoslinQC operator by Operator.get_by_class_name
        """
        operator = OperatorFactory.get_by_class_name("RoslinQcOperator", "foo")
        self.assertTrue(isinstance(operator, RoslinQcOperator))
        self.assertTrue( operator.pipeline_id == "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a")
        self.assertTrue( operator.operator == "roslin-qc")
        self.assertTrue( operator.request_id == "foo")
        self.assertTrue( operator._jobs == [])
        self.assertTrue( len(operator.files) == 0)

    # disable job submission to Ridgeback
    @patch('runner.tasks.submit_job')
    def test_direct_operator_creation(self, submit_job):
        """
        Test direct Operator instantiation without Operator Factory
        """
        # self.maxDiff = None
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        # create the operator instance
        operator = RoslinQcOperator(request_id = None, run_ids = ['ca18b090-03ad-4bef-acd3-52600f8e62eb'])

        # check its attributes
        self.assertEqual(operator.run_ids, ['ca18b090-03ad-4bef-acd3-52600f8e62eb'])
        self.assertEqual(operator.get_pipeline_id(), "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a")

        # create the data for the operator run
        input_data = operator.get_input_data()
        expected_input_data = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.roslin-qc.input.json")))

        output_metadata = operator.get_output_metadata()
        serializer_data = operator.get_data_for_serializer(input_data, output_metadata, name = "foo name")

        # check qualities of the data generated
        # need to pass data through JSON because loaded JSON fixtures do not represent Python tuples embedded in data
        self.assertEqual(json.loads(json.dumps(input_data)), expected_input_data)
        self.assertEqual(output_metadata, {})

        expected_serializer_data = {
            'app': "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a",
            'inputs': input_data,
            'name': "foo name",
            'tags': {'run_ids':['ca18b090-03ad-4bef-acd3-52600f8e62eb']},
            'output_metadata': output_metadata
            }
        self.assertEqual(serializer_data, expected_serializer_data)

        # create a run with the data
        self.assertEqual(len(Run.objects.all()), 1)
        jobs = operator.get_jobs()
        for job in jobs:
            if job[0].is_valid():
                run = job[0].save()
                create_run_task(str(run.id), job[1], None)
        self.assertEqual(len(Run.objects.all()), 2)
