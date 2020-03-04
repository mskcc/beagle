"""
Tests for Roslin QC Operator class
"""
import os
import json
from mock import patch
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from runner.operator.roslin_qc_operator.roslin_qc_operator import RoslinQcOperator
from beagle_etl.models import Operator
from django.conf import settings
from django.core.management import call_command
from runner.models import Pipeline, Run
from runner.tasks import create_run_task
from pprint import pprint

class TestRoslinQcOperator(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json",
    "beagle_etl.operator.json"
    ]

    def test_create_operator1(self):
        """
        Test that a Roslin QC operator instance can be created
        """
        pipeline_type = "roslin-qc"
        request_id = "foo"
        roslin_qc_model = Operator.objects.get(slug="roslin-qc")
        operator = RoslinQcOperator(roslin_qc_model, request_id = request_id)
        self.assertTrue(isinstance(operator, RoslinQcOperator))
        self.assertTrue( operator.request_id == "foo")
        self.assertTrue( operator._jobs == [])
        self.assertTrue( len(operator.files) == 0)

    # disable job submission to Ridgeback
    @patch('runner.tasks.submit_job')
    def test_direct_operator_creation(self, submit_job):
        """
        Test direct Operator instantiation without Operator Factory and try to create valid jobs
        """
        # self.maxDiff = None
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        # test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "roslin_reference_files.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        # create the operator instance
        roslin_qc_model = Operator.objects.get(slug="roslin-qc")
        operator = RoslinQcOperator(roslin_qc_model, run_ids = ['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2'])

        # check its attributes
        self.assertEqual(operator.run_ids, ['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2'])
        self.assertEqual(operator.get_pipeline_id(), "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a")

        # create the data for the operator run
        input_data = operator.get_input_data()
        # TODO: need way to recreate this for testing
        # expected_input_data = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.roslin-qc.input.json")))

        output_metadata = operator.get_output_metadata()
        serializer_data = operator.get_data_for_serializer(input_data, output_metadata, name = "foo name")
        # pprint(serializer_data, indent = 4, stream = open('roslin-qc-job.json', "w"))
        # print(json.dumps(serializer_data, indent = 4), file = open('roslin-qc-job.json', "w"))

        # check qualities of the data generated
        # need to pass data through JSON because loaded JSON fixtures do not represent Python tuples embedded in data
        # self.assertEqual(json.loads(json.dumps(input_data)), expected_input_data)
        # self.assertEqual(output_metadata, {})

        expected_serializer_data = {
            'app': "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a",
            'inputs': input_data,
            'name': "foo name",
            'tags': {'run_ids':['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2']},
            'output_metadata': output_metadata
            }
        self.assertEqual(serializer_data, expected_serializer_data)

        # create a run with the data
        # make sure only 1 run exists before starting
        self.assertEqual(len(Run.objects.all()), 1)

        # create and validate the jobs then use them to create Runs
        jobs = operator.get_jobs()
        for job in jobs:
            if job[0].is_valid():
                run = job[0].save()
                create_run_task(str(run.id), job[1], None)

        # make sure that a Run was made
        self.assertEqual(len(Run.objects.all()), 2)
