"""
Tests for Argos Operator class
"""
import os
from django.test import TestCase
from runner.operator.operator_factory import OperatorFactory
from beagle_etl.models import Operator
from django.conf import settings
from django.core.management import call_command
from file_system.models import File, FileMetadata, FileGroup, FileType
from pprint import pprint


class TestAlignmentPairOperator(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "beagle_etl.operator.json",
        "runner.pipeline.json",
    ]

    def test_operator_factory_alignment_pair1(self):
        """
        Test that a Alignment Pair operator can be created
        This test uses an empty database
        """

        request_id = "bar"
        operator_model = Operator.objects.get(id=18)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "a84c74ea-e129-496d-abb3-17a90dfe230b")
        self.assertEqual(str(operator.model), "argos")
        self.assertEqual(operator.request_id, "bar")
        self.assertEqual(operator._jobs, [])
        # no File items in the database yet
        self.assertEqual(len(operator.files), 0)

    def test_operator_factory_alignment_pair2(self):
        """
        Test that a Alignment Pair operator can be created
        This test loads some Alignment Pair fixtures and checks the number of Files available to the Operator
        """
        # Load fixtures; 4 fastq files for 2 patient samples
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        request_id = "bar"
        operator_model = Operator.objects.get(id=17)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "a84c74ea-e129-496d-abb3-17a90dfe230b")
        self.assertEqual(str(operator.model), "argos")
        self.assertEqual(operator.request_id, "bar")
        self.assertEqual(operator._jobs, [])
        self.assertEqual(len(operator.files), 4)

    def test_operator_factory_alignment_pair3(self):
        """
        Test that a Alignment Pair operator has access to all files in the database, even non-Argos files
        """
        # Load fixtures; 4 fastq files for 2 patient samples
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        self.assertEqual(len(File.objects.all()), 4)
        self.assertEqual(len(FileMetadata.objects.all()), 4)

        # create some more fixtures
        file_instance = File.objects.create(
            file_name="foo.fastq.gz",
            path="/foo.fastq.gz",
            file_group=FileGroup.objects.get(id=settings.IMPORT_FILE_GROUP),
        )
        filemetadata_instance = FileMetadata.objects.create_or_update(file=file_instance)

        self.assertEqual(len(File.objects.all()), 5)
        self.assertEqual(len(FileMetadata.objects.all()), 5)

        # create Alignment Pair operator
        request_id = "bar"

        operator_model = Operator.objects.get(id=17)
        operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
        self.assertEqual(operator.get_pipeline_id(), "a84c74ea-e129-496d-abb3-17a90dfe230b")
        self.assertEqual(str(operator.model), "AlignmentPair")
        self.assertEqual(operator.request_id, "bar")
        self.assertEqual(operator._jobs, [])
        self.assertEqual(len(operator.files), 5)
