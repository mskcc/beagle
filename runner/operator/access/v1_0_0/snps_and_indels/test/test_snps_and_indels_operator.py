import os
from mock import patch

from django.conf import settings
from django.test import TestCase
from django.core.management import call_command

from beagle_etl.models import Operator
from file_system.models import File, FileMetadata, FileGroup, FileType
from runner.operator.access.v1_0_0.snps_and_indels import AccessLegacySNVOperator
from runner.models import Run
from runner.tasks import create_run_task
from runner.operator.operator_factory import OperatorFactory


CURDIR = os.path.dirname(os.path.realpath(__file__))
TEST_FIXTURE_DIR = os.path.join([CURDIR, 'fixtures'])


class TestAccessSNVOperator(TestCase):

    fixtures = [
        "curated_normal_files.json",
        "curated_normals_file_group.json",
        "curated_normals_file_metadata.json",
        "curated_normals_file_storage.json",
        "files.json",
        "files_metadata.json",
        "operator_run.json",
        "ports.json",
        "runs.json",
    ]

    def test_access_legacy_snv_operator(self):
        """
        Test that an Access legacy SNV operator instance can be created and used
        """
        # Load fixtures
        for f in self.fixtures:
            test_files_fixture = os.path.join(TEST_FIXTURE_DIR, f)
            call_command('loaddata', test_files_fixture, verbosity=0)

        self.assertEqual(len(File.objects.all()), 4)
        self.assertEqual(len(FileMetadata.objects.all()), 4)

        # create access SNV operator
        request_id = "bar"

        operator_model = Operator.objects.get(id=1)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "cb5d793b-e650-4b7d-bfcd-882858e29cc5")
        self.assertEqual(str(operator.model), "access_legacy_snv")
        self.assertEqual(operator.request_id, "bar")
        self.assertEqual(operator._jobs, [])
        self.assertEqual(len(operator.files), 5)

        pipeline_type = "access_legacy_snv"
        request_id = "foo"
        access_legacy_snv_model = Operator.objects.get(slug=pipeline_type)

        # Todo: choose one of these two ways to do this:
        operator = AccessLegacySNVOperator(access_legacy_snv_model, request_id=request_id)
        operator = AccessLegacySNVOperator(access_legacy_snv_model, run_ids=['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2'])

        self.assertTrue(isinstance(operator, AccessLegacySNVOperator))
        self.assertTrue(operator.request_id == "foo")
        self.assertTrue(operator._jobs == [])
        self.assertTrue(len(operator.files) == 0)

        # check its attributes
        self.assertEqual(operator.run_ids, ['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2'])
        self.assertEqual(operator.get_pipeline_id(), "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a")

        # create the data for the operator run
        input_data = operator.get_sample_inputs()
        # TODO: need way to recreate this for testing
        # expected_input_data = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "ca18b090-03ad-4bef-acd3-52600f8e62eb.roslin-qc.input.json")))

        # output_metadata = operator.get_output_metadata()
        # serializer_data = operator.get_data_for_serializer(input_data, output_metadata, name="foo name")
        # pprint(serializer_data, indent = 4, stream = open('roslin-qc-job.json', "w"))
        # print(json.dumps(serializer_data, indent = 4), file = open('roslin-qc-job.json', "w"))

        # check qualities of the data generated
        # need to pass data through JSON because loaded JSON fixtures do not represent Python tuples embedded in data
        # self.assertEqual(json.loads(json.dumps(input_data)), expected_input_data)
        # self.assertEqual(output_metadata, {})

        # expected_serializer_data = {
        #     'app': "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a",
        #     'inputs': input_data,
        #     'name': "foo name",
        #     'tags': {'run_ids': ['aa0694f1-0109-4205-a6b2-63e3e1d7c0a2']},
        #     'output_metadata': output_metadata
        # }
        # self.assertEqual(serializer_data, expected_serializer_data)

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
