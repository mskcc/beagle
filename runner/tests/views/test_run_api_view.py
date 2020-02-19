"""
Tests for Run API View
"""
import os
from mock import patch
from django.test import TestCase
from runner.views.run_api_view import OperatorViewSet
from runner.models import Run
from django.conf import settings
from django.core.management import call_command

from pprint import pprint

import beagle_etl.celery
if beagle_etl.celery.app.conf['task_always_eager'] == False:
    beagle_etl.celery.app.conf['task_always_eager'] = True

class MockRequest(object):
    """
    empty object to simulate a 'request' object
    """
    pass

class TestRunAPIView(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json"
    ]

    def test_post_to_view1(self):
        """
        Test that data sent through the API view 'post' method returns a successful status and expected response
        """
        pipeline_name = 'roslin'
        request_ids = ['foo', 'bar']

        request = MockRequest()
        request.data = {}
        request.data['request_ids'] = request_ids
        request.data['pipeline_name'] = pipeline_name

        view = OperatorViewSet()
        response = view.post(request)

        self.assertEqual(response.data, {'details': "Operator Job submitted {}".format(request_ids)})
        self.assertEqual(response.status_code, 200)

    # disable job submission to Ridgeback
    @patch('runner.tasks.submit_job')
    def test_creates_runs1(self, submit_job):
        """
        Test that sending data through the API view 'post' method starts a Run
        Checks to make sure that a Run is successfully created
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "roslin_reference_files.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        number_of_runs = len(Run.objects.all())
        self.assertEqual(number_of_runs, 0)

        pipeline_name = 'roslin'
        request_ids = ['10075_D']

        request = MockRequest()
        request.data = {}
        request.data['request_ids'] = request_ids
        request.data['pipeline_name'] = pipeline_name

        view = OperatorViewSet()
        response = view.post(request)

        number_of_runs = len(Run.objects.all())
        self.assertEqual(number_of_runs, 1)
