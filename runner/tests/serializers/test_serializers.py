"""
Tests for serialzers
"""
from django.test import TestCase
from uuid import UUID
from runner.serializers import APIRunCreateSerializer
from runner.models import Run

class TestSerializers(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json"
    ]

    def test_create_run_serializer1(self):
        """
        Test that the API Run Create Serializer works and creates a Run
        """
        # start with 0 runs in the database
        self.assertEqual(len(Run.objects.all()), 0)

        # data to pass to serializer
        data = {
        'app': 'cb5d793b-e650-4b7d-bfcd-882858e29cc5',
        'inputs': [],
        'name': 'ROSLIN 10075_D, 1 of 1',
        'tags': {'requestId': '10075_D'}
        }

        # run the serialzer
        serializer = APIRunCreateSerializer(data = data)
        serializer.is_valid()
        run = serializer.save()

        # should be a Run in the database now
        self.assertEqual(len(Run.objects.all()), 1)

        run_instance = Run.objects.all()[0]
        self.assertEqual(run_instance.app_id, UUID('cb5d793b-e650-4b7d-bfcd-882858e29cc5'))
        self.assertTrue(run_instance.name.startswith(data['name']))
        self.assertEqual(run_instance.tags, {'requestId': '10075_D'})
        self.assertEqual(run_instance.status, 0)

    def test_create_run_with_output_metadata1(self):
        """
        Test that output_metadata propagates to the Run instance created
        """
        data = {
        'app': 'cb5d793b-e650-4b7d-bfcd-882858e29cc5',
        'inputs': [],
        'name': 'foo Run',
        'output_metadata': {'assay':'IMPACT486'}
        }
        serializer = APIRunCreateSerializer(data = data)
        serializer.is_valid()
        run = serializer.save()
        run_instance = Run.objects.all()[0]
        self.assertEqual(run_instance.app_id, UUID('cb5d793b-e650-4b7d-bfcd-882858e29cc5'))
        self.assertTrue(run_instance.name.startswith(data['name']))
        self.assertEqual(run_instance.status, 0)
        self.assertEqual(run_instance.output_metadata, data['output_metadata'])
