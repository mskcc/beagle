"""
Tests for LIMS ETL jobs
"""
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from django.conf import settings
from beagle_etl.jobs.lims_etl_jobs import fetch_samples
from beagle_etl.jobs.lims_etl_jobs import create_pooled_normal
from beagle_etl.jobs.lims_etl_jobs import get_run_id_from_string
from file_system.models import File, FileGroup, FileMetadata, FileType
from beagle_etl.models import JobStatus, Job, Operator
from beagle_etl.tasks import scheduler
import beagle_etl.celery

# use local execution for Celery tasks
if beagle_etl.celery.app.conf['task_always_eager'] == False:
    beagle_etl.celery.app.conf['task_always_eager'] = True

class TestFetchSamples(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def test_true(self):
        self.assertTrue(True)

    def test_fetch_samples1(self):
        """
        Test fetching samples for a request from IGO LIMS
        Should import Pooled Normal samples automatically
        """
        # sanity check that starting db is empty
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        jobs = Job.objects.all()
        self.assertTrue(len(files) == 0)
        self.assertTrue(len(files_metadata) == 0)
        self.assertTrue(len(jobs) == 0)

        request_id = "10075_D"
        child_jobs = fetch_samples(request_id = request_id)

        # check that jobs were created successfully
        jobs = Job.objects.all()
        job_ids = [ job.id for job in jobs ]
        self.assertTrue(len(jobs) == len(child_jobs))
        self.assertTrue(len(jobs) == 17)
        for child_job in child_jobs:
            self.assertTrue(UUID(child_job) in job_ids)

        # need to run the job scheduler at least twice to completely process all jobs
        # TODO: need to split apart the IGO LIMS query from the sample import logic, so we can pass in mock JSON blob representing expected IGO LIMS API response to avoid having to actually query the real API for testing
        print(">>> running job scheduler")
        scheduler()
        scheduler()
        scheduler()
        print(">>> job scheduler complete")

        # check that all jobs completed successfully
        jobs = Job.objects.all()
        for job in jobs:
            self.assertTrue(job.status == JobStatus.COMPLETED)

        # check for updated files in the database
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 22)
        self.assertTrue(len(files_metadata) == 22)
        # TODO: need to validate that the correct number of pooled normal, normal, and tumor samples were imported

class TestCreatePooledNormal(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def test_true(self):
        self.assertTrue(True)

    def test_create_pooled_normal1(self):
        """
        Test the creation of a pooled normal entry in the database
        """
        # sanity check that starting db is empty
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 0)
        self.assertTrue(len(files_metadata) == 0)

        filepath = "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_POOLEDNORMALS/Sample_FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG/FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG_S5_R1_001.fastq.gz"
        file_group_id = str(settings.IMPORT_FILE_GROUP)

        create_pooled_normal(filepath, file_group_id)

        # check that files are now in the database
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 1)
        self.assertTrue(len(files_metadata) == 1)

        imported_file = File.objects.get(path = filepath)
        imported_file_metadata = FileMetadata.objects.get(file = imported_file)
        self.assertTrue(imported_file_metadata.metadata['preservation'] == 'FFPE')
        self.assertTrue(imported_file_metadata.metadata['recipe'] == 'IMPACT468')
        self.assertTrue(imported_file_metadata.metadata['runId'] == 'JAX_0397')
        # TODO: update 'runId' field, add more metadata fields

    def test_create_pooled_normal2(self):
        """
        Test the creation of a pooled normal entry in the database
        """
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/PITT_0439_BHFTCNBBXY/Project_POOLEDNORMALS/Sample_FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG/FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG_S7_R2_001.fastq.gz"
        file_group_id = str(settings.IMPORT_FILE_GROUP)
        create_pooled_normal(filepath, file_group_id)
        imported_file = File.objects.get(path = filepath)
        imported_file_metadata = FileMetadata.objects.get(file = imported_file)
        self.assertTrue(imported_file_metadata.metadata['preservation'] == 'FROZEN')
        self.assertTrue(imported_file_metadata.metadata['recipe'] == 'IMPACT468')
        self.assertTrue(imported_file_metadata.metadata['runId'] == 'PITT_0439')

class TestGetRunID(TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_get_run_id_from_string1(self):
        string = "PITT_0439_BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == 'PITT_0439')

    def test_get_run_id_from_string2(self):
        string = "foo_BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == 'foo')

    def test_get_run_id_from_string2(self):
        string = "BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == 'BHFTCNBBXY')
