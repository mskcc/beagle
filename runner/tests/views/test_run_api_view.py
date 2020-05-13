"""
Tests for Run API View
"""
import os
from mock import patch
from unittest.mock import Mock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from runner.views.run_api_view import OperatorViewSet
from runner.models import Run, RunStatus
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from pprint import pprint

import beagle_etl.celery
if beagle_etl.celery.app.conf['task_always_eager'] == False:
    beagle_etl.celery.app.conf['task_always_eager'] = True


class MockRequest(object):
    """
    empty object to simulate a 'request' object
    """
    pass

class TestRunAPIList(APITestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json",
    "beagle_etl.operator.json",
    "runner.operator_run.json",
    "runner.run.json",
    "runner.operator_trigger.json",]

    def setUp(self):
        self.api_root = reverse('run-list')
        admin_user = User.objects.create_superuser('admin', 'sample_email', 'password')
        self.client.force_authenticate(user=admin_user)

    def test_request_id_list(self):
        url = self.api_root + '?request_ids=request1&request_ids=request2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

    def test_single_request_id(self):
        url = self.api_root + '?request_ids=request1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_request_id_comma_format(self):
        url = self.api_root + '?request_ids=request1,request2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

    def test_multiple_query(self):
        url = self.api_root + '?request_ids=request1&status=CREATING'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 1)

    def test_tag(self):
        url = self.api_root + '?tags=tag:value'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 2)

    def test_date(self):
        url = self.api_root + '?created_after=2019-10-08T22:59:41.044Z'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 7)


class TestRunAPIView(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "beagle_etl.operator.json",
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
