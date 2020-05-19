"""
Tests for LIMS ETL jobs
"""

import os
import json
from mock import patch
from unittest import skipIf
from uuid import UUID
from django.test import TestCase
from django.conf import settings
from beagle_etl.tasks import scheduler
from beagle_etl.models import JobStatus, Job
from beagle_etl.exceptions import FailedToFetchFilesException
from rest_framework.test import APITestCase
from file_system.repository import FileRepository
from file_system.models import File, FileMetadata
from file_system.models import FileGroup, Storage, StorageType
from beagle_etl.jobs.lims_etl_jobs import create_pooled_normal, fetch_sample_metadata, get_run_id_from_string, fetch_samples

# use local execution for Celery tasks
# if beagle_etl.celery.app.conf['task_always_eager'] == False:
#     beagle_etl.celery.app.conf['task_always_eager'] = True


class TestFetchSamples(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    @skipIf(not (os.environ.get('BEAGLE_LIMS_USERNAME', None) and os.environ.get('BEAGLE_LIMS_PASSWORD', None)),
            'Skip if username or password for LIMS are not provided')
    def test_fetch_samples1(self):
        """
        Test fetching samples for a request from IGO LIMS
        Should import Pooled Normal samples automatically
        TODO: Mock LIMS API for this test and then remove skip
        """
        # sanity check that starting db is empty
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        jobs = Job.objects.all()
        self.assertTrue(len(files) == 0)
        self.assertTrue(len(files_metadata) == 0)
        self.assertTrue(len(jobs) == 0)

        request_id = "10075_D"
        child_jobs = fetch_samples(request_id=request_id)

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

        import_files = File.objects.filter(file_group=settings.IMPORT_FILE_GROUP)
        import_files_metadata = FileMetadata.objects.filter(file__in=[i.id for i in import_files])
        pooled_normal_files = File.objects.filter(file_group=settings.POOLED_NORMAL_FILE_GROUP)
        pooled_normal_files_metadata = FileMetadata.objects.filter(file__in=[i.id for i in pooled_normal_files])
        self.assertTrue(len(import_files) == 10)
        self.assertTrue(len(import_files_metadata) == 10)
        self.assertTrue(len(pooled_normal_files) == 12)
        self.assertTrue(len(pooled_normal_files_metadata) == 12)


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
        file_group_id = str(settings.POOLED_NORMAL_FILE_GROUP)

        create_pooled_normal(filepath, file_group_id)

        # check that files are now in the database
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 1)
        self.assertTrue(len(files_metadata) == 1)

        imported_file = File.objects.get(path=filepath)
        imported_file_metadata = FileMetadata.objects.get(file=imported_file)
        self.assertTrue(imported_file_metadata.metadata['preservation'] == 'FFPE')
        self.assertTrue(imported_file_metadata.metadata['recipe'] == 'IMPACT468')
        self.assertTrue(imported_file_metadata.metadata['runId'] == 'JAX_0397')
        # TODO: add more metadata fields?

    def test_create_pooled_normal2(self):
        """
        Test the creation of a pooled normal entry in the database
        """
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/PITT_0439_BHFTCNBBXY/Project_POOLEDNORMALS/Sample_FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG/FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG_S7_R2_001.fastq.gz"
        file_group_id = str(settings.POOLED_NORMAL_FILE_GROUP)
        create_pooled_normal(filepath, file_group_id)
        imported_file = File.objects.get(path=filepath)
        imported_file_metadata = FileMetadata.objects.get(file=imported_file)
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


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestImportSample(APITestCase):

    def setUp(self):
        self.storage = Storage.objects.create(name="LOCAL", type=StorageType.LOCAL)
        self.job_group = FileGroup.objects.create(name="LIMS", storage=self.storage)
        self.old_val = settings.IMPORT_FILE_GROUP
        settings.IMPORT_FILE_GROUP = str(self.job_group.id)
        self.data_1_fastq = [
            {
                "igoId": "igoId_001",
                "cmoSampleName": "sampleName_001-d",
                "sampleName": "sampleName_001-d",
                "cmoSampleClass": "Normal",
                "cmoPatientId": "patientId-001",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                "oncoTreeCode": None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                "specimenType": "Blood",
                "sampleOrigin": "Whole Blood",
                "preservation": "Blood",
                "collectionYear": "2016",
                "sex": "M",
                "species": "Human",
                "cfDNA2dBarcode": None,
                "baitSet": "SureSelect-All-Exon-V4-hg19",
                "qcReports": [],
                "libraries": [
                    {
                        "barcodeId": "IDT36",
                        "barcodeIndex": "CCAGTTCA",
                        "libraryIgoId": "igoId_001_1",
                        "libraryVolume": None,
                        "libraryConcentrationNgul": 2.2051049976353,
                        "dnaInputNg": None,
                        "captureConcentrationNm": None,
                        "captureInputNg": None,
                        "captureName": None,
                        "runs": [
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_001",
                                "flowCellId": "HHJ5HBBXX",
                                "readLength": "",
                                "runDate": "2017-04-21",
                                "flowCellLanes": [
                                    8
                                ],
                                "fastqs": [
                                    "/path/to/sample/10/sampleName_001-d_IGO_igoId_002_S728_L008_R2_001.fastq.gz",
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        self.data_2_fastq = [
            {
                "igoId": "igoId_002",
                "cmoSampleName": "sampleName_002-d",
                "sampleName": "sampleName_002-d",
                "cmoSampleClass": "Normal",
                "cmoPatientId": "patientId-002",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                "oncoTreeCode": None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                "specimenType": "Blood",
                "sampleOrigin": "Whole Blood",
                "preservation": "Blood",
                "collectionYear": "2016",
                "sex": "M",
                "species": "Human",
                "cfDNA2dBarcode": None,
                "baitSet": "SureSelect-All-Exon-V4-hg19",
                "qcReports": [],
                "libraries": [
                    {
                        "barcodeId": "IDT36",
                        "barcodeIndex": "CCAGTTCA",
                        "libraryIgoId": "igoId_002_1",
                        "libraryVolume": None,
                        "libraryConcentrationNgul": 2.2051049976353,
                        "dnaInputNg": None,
                        "captureConcentrationNm": None,
                        "captureInputNg": None,
                        "captureName": None,
                        "runs": [
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_002",
                                "flowCellId": "HHJ5HBBXX",
                                "readLength": "",
                                "runDate": "2017-04-21",
                                "flowCellLanes": [
                                    8
                                ],
                                "fastqs": [
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R1_001.fastq.gz"
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        self.data_6_fastq = [
            {
                "igoId": "igoId_006",
                "cmoSampleName": "sampleName_006",
                "sampleName": "sampleName_006",
                "cmoSampleClass": "Metastasis",
                "cmoPatientId": "patientId_006",
                "investigatorSampleId": "InvestigatorSampleId-T01-WES",
                "oncoTreeCode": "PRAD",
                "tumorOrNormal": "Tumor",
                "tissueLocation": "Prostate",
                "specimenType": "Resection",
                "sampleOrigin": "Block",
                "preservation": "FFPE",
                "collectionYear": "2015",
                "sex": "M",
                "species": "Human",
                "cfDNA2dBarcode": None,
                "baitSet": "SureSelect-All-Exon-V4-hg19",
                "qcReports": [],
                "libraries": [
                    {
                        "barcodeId": "IDT59",
                        "barcodeIndex": "GTGTTCTA",
                        "libraryIgoId": "igoId_006_1",
                        "libraryVolume": None,
                        "libraryConcentrationNgul": 1.89855144270164,
                        "dnaInputNg": None,
                        "captureConcentrationNm": None,
                        "captureInputNg": None,
                        "captureName": None,
                        "runs": [
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_0061",
                                "flowCellId": "HHGYTBBXX",
                                "readLength": "",
                                "runDate": "2017-04-25",
                                "flowCellLanes": [
                                    6,
                                    7
                                ],
                                "fastqs": [
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R2_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R1_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R1_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R2_001.fastq.gz"
                                ]
                            },
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_0062",
                                "flowCellId": "HHN7YBBXX",
                                "readLength": "",
                                "runDate": "2017-05-05",
                                "flowCellLanes": [
                                    3
                                ],
                                "fastqs": [
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz"
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def tearDown(self):
        settings.IMPORT_FILE_GROUP = self.old_val

    @patch('requests.get')
    def test_import_sample_two_fastq_files(self, mock_get_sample):
        mock_get_sample.return_value = MockResponse(json_data=self.data_2_fastq, status_code=200)
        fetch_sample_metadata('igoId_002', True, 'sampleName_002', {})
        count_files = FileRepository.filter(path_in=[
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R1_001.fastq.gz"
                                ]).count()
        self.assertEqual(count_files, 2)

    @patch('requests.get')
    def test_import_sample_six_fastq_files(self, mock_get_sample):
        mock_get_sample.return_value = MockResponse(json_data=self.data_6_fastq, status_code=200)
        fetch_sample_metadata('igoId_006', True, 'sampleName_006', {})
        count_files = FileRepository.filter(path_in=[
            "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R2_001.fastq.gz",
            "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R1_001.fastq.gz",
            "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R1_001.fastq.gz",
            "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R2_001.fastq.gz",
            "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
            "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz"
        ]).count()
        self.assertEqual(count_files, 6)

    @patch('requests.get')
    def test_invalid_number_of_fastq_files(self, mock_get_sample):
        mock_get_sample.return_value = MockResponse(json_data=self.data_1_fastq, status_code=200)
        with self.assertRaises(FailedToFetchFilesException) as e:
            fetch_sample_metadata('igoId_001', True, 'sampleName_001', {})
        count_files = FileRepository.filter(path_in=[
            "/path/to/sample/10/sampleName_001-d_IGO_igoId_002_S728_L008_R2_001.fastq.gz"
        ]).count()
        self.assertEqual(count_files, 0)
