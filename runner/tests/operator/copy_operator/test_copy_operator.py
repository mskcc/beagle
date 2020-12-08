"""
Test cases for Copy Operator
"""
import os
from django.test import TestCase
from beagle_etl.models import Operator
from file_system.models import File, FileMetadata, FileGroup
from runner.models import Run, Pipeline
from runner.views.run_api_view import OperatorViewSet
from runner.operator.operator_factory import OperatorFactory
from runner.operator.copy_operator.copy_operator import CopyOperator
from runner.tasks import check_jobs_status
from tempfile import mkdtemp
import shutil
from mock import patch
from django.conf import settings
import time
from pprint import pprint

# Run Celery tasks synchronously for testing, no async
import beagle_etl.celery
if beagle_etl.celery.app.conf['task_always_eager'] == False:
    beagle_etl.celery.app.conf['task_always_eager'] = True

class MockRequest(object):
    """
    empty object to simulate a 'request' object; apply a 'data' attribute to this later
    """
    pass

class TestCopyOperator(TestCase):
    def setUp(self):
        settings.NOTIFIER_ACTIVE = False

        # needed for making File entries in the db
        self.filegroup = FileGroup.objects.create(
            name = 'demo_filegroup',
            slug = 'demo_filegroup'
        )


        # db entry for the Operator we want to test
        self.operator = Operator.objects.create(
            slug = 'CopyOperator',
            class_name = 'runner.operator.copy_operator.copy_operator.CopyOperator',
            version = "1",
            active = True,
            recipes = []
        )

        # make a tmpdir and put a file in it
        self.tmpdir = mkdtemp()
        self.tmp_path = os.path.join(self.tmpdir, "foo.txt")
        self.output_dir = os.path.join(self.tmpdir, "output")
        os.mkdir(self.output_dir)
        with open(self.tmp_path, "w") as f:
            f.write("some data\n")

        # add the file to the db
        self.file1 = File.objects.create(
            file_name = os.path.basename(self.tmp_path),
            path = self.tmp_path,
            file_group = self.filegroup
        )
        self.fileMetadata1 = FileMetadata.objects.create(
            file = self.file1,
            metadata = {'requestId' : '1'}
        )

        # add a second file to the db
        self.tmp_path2 = os.path.join(self.tmpdir, "bar.txt")
        with open(self.tmp_path2, "w") as f:
            f.write("some more data\n")
        self.file2 = File.objects.create(
            file_name = os.path.basename(self.tmp_path2),
            path = self.tmp_path2,
            file_group = self.filegroup
        )
        self.fileMetadata2 = FileMetadata.objects.create(
            file = self.file2,
            metadata = {'requestId' : '2'}
        )

        # Pipeline entry for the Operator
        self.pipeline = Pipeline.objects.create(
            name = CopyOperator._pipeline_name,
            github = "git@github.com:stevekm/copy-cwl",
            version = "master",
            entrypoint = "copy.cwl",
            output_file_group = self.filegroup,
            output_directory = self.output_dir,
            operator = self.operator
        )


    def tearDown(self):
        # remove the tmpdir upon test completion
        shutil.rmtree(self.tmpdir)

    def test_get_copy_operator(self):
        """
        Test that CopyOperator can be initialized
        """
        operator_instance = self.operator
        operator = OperatorFactory.get_by_model(operator_instance)
        self.assertEqual(str(operator.model), "CopyOperator")

    def test_copy_operator_input(self):
        """
        Test that input data can be generated from Copy Operator
        """
        request_id = '1'
        operator_instance = self.operator
        operator = OperatorFactory.get_by_model(operator_instance, request_id = request_id)
        run_input = operator.create_input()
        expected_input = {
            'class': 'File',
            'path': self.file1.path
            }
        self.assertDictEqual(run_input, expected_input)

    # disable job submission to Ridgeback
    @patch('runner.tasks.submit_job')
    def test_create_copy_operator_run(self, submit_job):
        """
        Test case for creating a Copy Operator run
        """
        # there should be no Runs
        number_of_runs = len(Run.objects.all())
        self.assertEqual(number_of_runs, 0)

        # make a fake http request with some data
        # and send it to the API endpoint for starting a run
        request = MockRequest()
        request.data = {
            'request_ids': ['1'],
            'pipeline_name': CopyOperator._pipeline_name
            }
        view = OperatorViewSet()
        response = view.post(request)

        # there should be 1 run now
        number_of_runs = len(Run.objects.all())
        self.assertEqual(number_of_runs, 1)


    def test_live_copy_operator_run(self):
        """
        A test case for submitting a job to Ridgeback for a custom file that is passed from the environment

        $ COPY_FILE=1 python manage.py test runner.tests.operator.copy_operator.test_copy_operator.TestCopyOperator.test_live_copy_operator_run
        """
        enable_testcase = os.environ.get('COPY_FILE')
        request_id = 'test_live_copy_operator_run'

        if enable_testcase:
            print(">>> running TestCopyOperator.test_live_copy_operator_run")

            # make a file
            path = os.path.join(self.tmpdir, "file.txt")
            with open(path, 'w') as f:
                f.write('some data\n')

            # make db entries
            file_instance = File.objects.create(
                file_name = os.path.basename(path),
                path = path,
                file_group = self.filegroup
            )
            filemetadata_instance = FileMetadata.objects.create(
                file = file_instance,
                metadata = {'requestId' : request_id}
            )

            # make a request to start the run
            request = MockRequest()
            request.data = {
                'request_ids': [request_id],
                'pipeline_name': CopyOperator._pipeline_name
                }
            view = OperatorViewSet()
            response = view.post(request)
            print(">>> response: ", response, response.data)

            self.assertEqual(response.status_code, 200)

            # there should be 1 run now
            self.assertEqual(len(Run.objects.all()), 1)
            run_instance = Run.objects.all().first()

            count = 0
            while True:
                count += 1
                print('>>> checking job status ({})'.format(count))
                check_jobs_status()
                pprint(run_instance.__dict__, indent = 4)
                time.sleep(5)
