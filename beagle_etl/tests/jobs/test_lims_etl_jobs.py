"""
Tests for LIMS ETL jobs
"""


from mock import patch, call
from datetime import date
from django.test import TestCase
from django.conf import settings
from beagle_etl.models import ETLConfiguration
from rest_framework.test import APITestCase
from runner.models import Operator
from notifier.models import JobGroup, JobGroupNotifier, Notifier
from file_system.models import File, FileMetadata, FileType, FileGroup, Storage, StorageType
from beagle_etl.jobs.metadb_jobs import (
    create_pooled_normal,
    get_run_id_from_string,
    request_callback,
    fetch_operators_wfastq,
)


class TestFetchSamples(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    # @skipIf(not (os.environ.get('BEAGLE_LIMS_USERNAME', None) and os.environ.get('BEAGLE_LIMS_PASSWORD', None)),
    #         'Skip if username or password for LIMS are not provided')
    # TODO: Refactor test for SMILE integration
    # def test_fetch_samples1(self):
    #     """
    #     Test fetching samples for a request from IGO LIMS
    #     Should import Pooled Normal samples automatically
    #     TODO: Mock LIMS API for this test and then remove skip
    #     """
    #     # sanity check that starting db is empty
    #     files = File.objects.all()
    #     files_metadata = FileMetadata.objects.all()
    #     jobs = Job.objects.all()
    #     self.assertTrue(len(files) == 0)
    #     self.assertTrue(len(files_metadata) == 0)
    #     self.assertTrue(len(jobs) == 0)
    #
    #     request_id = "10075_D"
    #     # child_jobs = fetch_samples(request_id=request_id)
    #
    #     # check that jobs were created successfully
    #     jobs = Job.objects.all()
    #     job_ids = [ job.id for job in jobs ]
    #     self.assertTrue(len(jobs) == len(child_jobs))
    #     self.assertTrue(len(jobs) == 17)
    #     for child_job in child_jobs:
    #         self.assertTrue(UUID(child_job) in job_ids)
    #
    #     # need to run the job scheduler at least twice to completely process all jobs
    #     # TODO: need to split apart the IGO LIMS query from the sample import logic, so we can pass in mock JSON blob representing expected IGO LIMS API response to avoid having to actually query the real API for testing
    #     print(">>> running job scheduler")
    #     scheduler()
    #     scheduler()
    #     scheduler()
    #     print(">>> job scheduler complete")
    #
    #     # check that all jobs completed successfully
    #     jobs = Job.objects.filter(run='beagle_etl.jobs.lims_etl_jobs.create_pooled_normal').all()
    #     for job in jobs:
    #         print("%s %s" % (job.run, JobStatus(job.status).name))
    #         self.assertTrue(job.status == JobStatus.COMPLETED)

    # check for updated files in the database
    # files = File.objects.all()
    # files_metadata = FileMetadata.objects.all()
    # self.assertTrue(len(files) == 22)
    # self.assertTrue(len(files_metadata) == 22)

    # import_files = File.objects.filter(file_group=settings.IMPORT_FILE_GROUP)
    # import_files_metadata = FileMetadata.objects.filter(file__in=[i.id for i in import_files])
    # pooled_normal_files = File.objects.filter(file_group=settings.POOLED_NORMAL_FILE_GROUP)
    # pooled_normal_files_metadata = FileMetadata.objects.filter(file__in=[i.id for i in pooled_normal_files])
    # self.assertTrue(len(import_files) == 10)
    # self.assertTrue(len(import_files_metadata) == 10)
    # self.assertTrue(len(pooled_normal_files) == 12)
    # self.assertTrue(len(pooled_normal_files_metadata) == 12)


class TestCreatePooledNormal(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        self.storage = Storage.objects.create(name="LOCAL", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name=settings.POOLED_NORMAL_FILE_GROUP, storage=self.storage)
        assay = ETLConfiguration.objects.first()
        self.disabled_backup = assay.disabled_recipes
        assay.all = ["IMPACT468", "HemePACT", "HemePACT_v4", "DisabledAssay"]
        assay.disabled = ["DisabledAssay"]
        assay.save()

    def test_true(self):
        self.assertTrue(True)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_create_pooled_normal1(self, populate_job_group_notifier_metadata):
        """
        Test the creation of a pooled normal entry in the database
        """
        # sanity check that starting db is empty
        populate_job_group_notifier_metadata.return_value = True
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 0)
        self.assertTrue(len(files_metadata) == 0)

        filepath = "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_POOLEDNORMALS/Sample_FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG/FFPEPOOLEDNORMAL_IGO_IMPACT468_GTGAAGTG_S5_R1_001.fastq.gz"

        create_pooled_normal(filepath, self.file_group.id)

        # check that files are now in the database
        files = File.objects.all()
        files_metadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 1)
        self.assertTrue(len(files_metadata) == 1)

        imported_file = File.objects.get(path=filepath)
        imported_file_metadata = FileMetadata.objects.get(file=imported_file)
        self.assertTrue(imported_file_metadata.metadata["preservation"] == "FFPE")
        self.assertTrue(imported_file_metadata.metadata[settings.RECIPE_METADATA_KEY] == "IMPACT468")
        self.assertTrue(imported_file_metadata.metadata["runId"] == "JAX_0397")
        # TODO: add more metadata fields?

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_create_pooled_normal2(self, populate_job_group_notifier_metadata):
        """
        Test the creation of a pooled normal entry in the database
        """
        populate_job_group_notifier_metadata.return_value = True
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/PITT_0439_BHFTCNBBXY/Project_POOLEDNORMALS/Sample_FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG/FROZENPOOLEDNORMAL_IGO_IMPACT468_CTAACTCG_S7_R2_001.fastq.gz"
        create_pooled_normal(filepath, self.file_group.id)
        imported_file = File.objects.get(path=filepath)
        imported_file_metadata = FileMetadata.objects.get(file=imported_file)
        self.assertTrue(imported_file_metadata.metadata["preservation"] == "FROZEN")
        self.assertTrue(imported_file_metadata.metadata[settings.RECIPE_METADATA_KEY] == "IMPACT468")
        self.assertTrue(imported_file_metadata.metadata["runId"] == "PITT_0439")

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_create_pooled_normal_recipe(self, populate_job_group_notifier_metadata):
        """
        Test the creation of a pooled normal entry in the database with the right recipe
        """
        populate_job_group_notifier_metadata.return_value = True
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/PITT_0439_BHFTCNBBXY/Project_POOLEDNORMALS/Sample_FROZENPOOLEDNORMAL_IGO_HemePACT_v4_CTAACTCG/FROZENPOOLEDNORMAL_IGO_HemePACT_v4_CTAACTCG_S7_R2_001.fastq.gz"
        create_pooled_normal(filepath, self.file_group.id)
        imported_file = File.objects.get(path=filepath)
        imported_file_metadata = FileMetadata.objects.get(file=imported_file)
        self.assertTrue(imported_file_metadata.metadata[settings.RECIPE_METADATA_KEY] == "HemePACT_v4")

    def test_create_pooled_normal_disabled_recipe(self):
        """
        Test the rejection of the creation of a pooled normal with a disabled recipe
        """
        filepath = "/ifs/archive/GCL/hiseq/FASTQ/PITT_0439_BHFTCNBBXY/Project_POOLEDNORMALS/Sample_FROZENPOOLEDNORMAL_IGO_DisabledAssay_CTAACTCG/FROZENPOOLEDNORMAL_IGO_DisabledAssay_CTAACTCG_S7_R2_001.fastq.gz"
        imported_file = File.objects.filter(path=filepath)
        self.assertEqual(imported_file.count(), 0)


class TestGetRunID(TestCase):
    def test_true(self):
        self.assertTrue(True)

    def test_get_run_id_from_string1(self):
        string = "PITT_0439_BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == "PITT_0439")

    def test_get_run_id_from_string2(self):
        string = "foo_BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == "foo")

    def test_get_run_id_from_string2(self):
        string = "BHFTCNBBXY"
        runID = get_run_id_from_string(string)
        self.assertTrue(runID == "BHFTCNBBXY")


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestImportSample(APITestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="LOCAL", type=StorageType.LOCAL)
        self.fastq = FileType.objects.create(name="fastq")
        self.file_group = FileGroup.objects.create(name="LIMS", storage=self.storage)
        self.old_val = settings.IMPORT_FILE_GROUP
        settings.IMPORT_FILE_GROUP = str(self.file_group.id)
        assay = ETLConfiguration.objects.first()
        self.disabled_backup = assay.disabled_recipes
        assay.all_recipes.append("DisabledAssay1")
        assay.all_recipes.append("DisabledAssay2")
        assay.all_recipes.append("TestAssay")
        assay.disabled_recipes = ["DisabledAssay1", "DisabledAssay2"]
        assay.save()
        self.data_0_fastq = [
            {
                "igoId": "igoId_000",
                "cmoSampleName": "sampleName_000-d",
                "sampleName": "sampleName_000-d",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                settings.PATIENT_ID_METADATA_KEY: "patientId-000",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                settings.ONCOTREE_METADATA_KEY: None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_000_1",
                        "libraryVolume": None,
                        "libraryConcentrationNgul": 2.2051049976353,
                        "dnaInputNg": None,
                        "captureConcentrationNm": None,
                        "captureInputNg": None,
                        "captureName": None,
                        "runs": [
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_000",
                                "flowCellId": "HHJ5HBBXX",
                                "readLength": "",
                                "runDate": "2017-04-21",
                                "flowCellLanes": [8],
                                "fastqs": [],
                            }
                        ],
                    }
                ],
            }
        ]
        self.data_1_fastq = [
            {
                "igoId": "igoId_001",
                "cmoSampleName": "sampleName_001-d",
                "sampleName": "sampleName_001-d",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                settings.PATIENT_ID_METADATA_KEY: "patientId-001",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                settings.ONCOTREE_METADATA_KEY: None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_001_1",
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
                                "flowCellLanes": [8],
                                "fastqs": [
                                    "/path/to/sample/10/sampleName_001-d_IGO_igoId_002_S728_L008_R2_001.fastq.gz",
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        self.data_2_fastq = [
            {
                "igoId": "igoId_002",
                "cmoSampleName": "sampleName_002-d",
                "sampleName": "sampleName_002-d",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                settings.PATIENT_ID_METADATA_KEY: "patientId-002",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                settings.ONCOTREE_METADATA_KEY: None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_002_1",
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
                                "flowCellLanes": [8],
                                "fastqs": [
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R1_001.fastq.gz",
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        self.data_6_fastq = [
            {
                "igoId": "igoId_006",
                "cmoSampleName": "sampleName_006",
                "sampleName": "sampleName_006",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Metastasis",
                settings.PATIENT_ID_METADATA_KEY: "patientId_006",
                "investigatorSampleId": "InvestigatorSampleId-T01-WES",
                settings.ONCOTREE_METADATA_KEY: "PRAD",
                "tumorOrNormal": "Tumor",
                "tissueLocation": "Prostate",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_006_1",
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
                                "flowCellLanes": [6, 7],
                                "fastqs": [
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R2_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R1_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R1_001.fastq.gz",
                                    "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R2_001.fastq.gz",
                                ],
                            },
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_0062",
                                "flowCellId": "HHN7YBBXX",
                                "readLength": "",
                                "runDate": "2017-05-05",
                                "flowCellLanes": [3],
                                "fastqs": [
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz",
                                ],
                            },
                        ],
                    }
                ],
            }
        ]
        self.data_2_fastq = [
            {
                "igoId": "igoId_002",
                "cmoSampleName": "sampleName_002-d",
                "sampleName": "sampleName_002-d",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                settings.PATIENT_ID_METADATA_KEY: "patientId-002",
                "investigatorSampleId": "InvestigatorSampleId-N01-WES",
                settings.ONCOTREE_METADATA_KEY: None,
                "tumorOrNormal": "Normal",
                "tissueLocation": "na",
                settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_002_1",
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
                                "flowCellLanes": [8],
                                "fastqs": [
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
                                    "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R1_001.fastq.gz",
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        self.data_conflict_fastq = [
            {
                "igoId": "igoId_006",
                "cmoSampleName": "sampleName_006",
                "sampleName": "sampleName_006",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Metastasis",
                settings.PATIENT_ID_METADATA_KEY: "patientId_006",
                "investigatorSampleId": "InvestigatorSampleId-T01-WES",
                settings.ONCOTREE_METADATA_KEY: "PRAD",
                "tumorOrNormal": "Tumor",
                "tissueLocation": "Prostate",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
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
                        settings.LIBRARY_ID_METADATA_KEY: "igoId_006_1",
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
                                "flowCellLanes": [6, 7],
                                "fastqs": [
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz",
                                ],
                            },
                            {
                                "runMode": "HiSeq High Output",
                                "runId": "runId_0062",
                                "flowCellId": "HHN7YBBXX",
                                "readLength": "",
                                "runDate": "2017-05-05",
                                "flowCellLanes": [3],
                                "fastqs": [
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
                                    "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz",
                                ],
                            },
                        ],
                    }
                ],
            }
        ]

    def tearDown(self):
        assay = ETLConfiguration.objects.first()
        assay.disabled_recipes = self.disabled_backup
        assay.save()
        settings.IMPORT_FILE_GROUP = self.old_val

    # @patch('requests.get')
    # TODO: Refactor test for SMILE integration
    # def test_zero_fastq_files(self, mock_get_sample):
    #     mock_get_sample.return_value = MockResponse(json_data=self.data_0_fastq, status_code=200)
    #     with self.assertRaises(ErrorInconsistentDataException) as e:
    #         fetch_sample_metadata('igoId_000', True, 'sampleName_000', {})
    #         self.assertTrue("Missing fastq files for igcomplete: " in str(e))
    #
    # @patch('requests.get')
    # def test_zero_samples_igocomplete_false(self, mock_get_sample):
    #     mock_get_sample.return_value = MockResponse(json_data=self.data_0_fastq, status_code=200)
    #     with self.assertRaises(MissingDataException):
    #         fetch_sample_metadata('igoId_000', False, 'sampleName_000', {})
    #     count_files = FileRepository.all().count()
    #     self.assertEqual(count_files, 0)
    #
    # @patch('requests.get')
    # def test_import_sample_two_fastq_files(self, mock_get_sample):
    #     mock_get_sample.return_value = MockResponse(json_data=self.data_2_fastq, status_code=200)
    #     fetch_sample_metadata('igoId_002', True, 'sampleName_002', {})
    #     count_files = FileRepository.filter(path_in=[
    #                                 "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
    #                                 "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R1_001.fastq.gz"
    #                             ]).count()
    #     self.assertEqual(count_files, 2)
    #
    # @patch('requests.get')
    # def test_import_sample_six_fastq_files(self, mock_get_sample):
    #     mock_get_sample.return_value = MockResponse(json_data=self.data_6_fastq, status_code=200)
    #     fetch_sample_metadata('igoId_006', True, 'sampleName_006', {})
    #     count_files = FileRepository.filter(path_in=[
    #         "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R2_001.fastq.gz",
    #         "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L007_R1_001.fastq.gz",
    #         "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R1_001.fastq.gz",
    #         "/path/to/sample/01/sampleName_006_IGO_igoId_006_S64_L006_R2_001.fastq.gz",
    #         "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R1_001.fastq.gz",
    #         "/path/to/sample/02/sampleName_006_IGO_igoId_006_S54_L003_R2_001.fastq.gz"
    #     ]).count()
    #     self.assertEqual(count_files, 6)
    #
    # @patch('requests.get')
    # def test_file_conflict(self, mock_get_sample):
    #     file_conflict = File.objects.create(
    #         path="/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
    #         file_type=self.fastq,
    #         file_group=self.file_group,
    #         )
    #     file_metadata = FileMetadata.objects.create(file=file_conflict, version=1, metadata={})
    #     mock_get_sample.return_value = MockResponse(json_data=self.data_2_fastq, status_code=200)
    #     with self.assertRaises(ErrorInconsistentDataException) as e:
    #         fetch_sample_metadata('igoId_002', True, 'sampleName_002', {})
    #         self.assertTrue('Conflict of fastq file(s)' in str(e))
    #     count_files = FileRepository.filter(path_in=[
    #         "/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
    #     ]).count()
    #     self.assertEqual(count_files, 1)

    @patch("runner.tasks.create_jobs_from_request.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("notifier.tasks.send_notification.delay")
    @patch("beagle_etl.jobs.metadb_jobs.request_update_notification")
    def test_request_callback(
        self,
        request_update_notification,
        send_notification,
        populate_job_group_notifier_metadata,
        mock_create_jobs_from_request,
    ):
        request_update_notification.return_value = None
        populate_job_group_notifier_metadata.return_value = True
        send_notification.return_value = True
        job_group = JobGroup.objects.create()
        notifier = Notifier.objects.create(default=False, notifier_type="JIRA", board="IMPORT")
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group, notifier_type=notifier)
        file_conflict = File.objects.create(
            path="/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
            file_type=self.fastq,
            file_group=self.file_group,
        )
        date_now = date.today().strftime("%Y-%m-%d")
        file_metadata = FileMetadata.objects.create_or_update(
            file=file_conflict,
            version=1,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: "test1",
                "genePanel": "TestAssay",
                "labHeadEmail": "test@email.com",
                "runDate": date_now,
                "baitSet": "TestBait",
            },
        )
        operator1 = Operator.objects.create(
            slug="Operator1",
            class_name="Operator",
            recipes=["TestAssay"],
            recipes_json=[
                {"genePanel": ["TestAssay", "TestAssay2"], "baitSet": "TestBait"},
                {"genePanel": "TestAssay3", "baitSet": "TestBait2"},
            ],
            active=True,
        )
        request_callback(
            "test1", "TestAssay", file_metadata.metadata, [], str(job_group.id), str(job_group_notifier.id)
        )
        mock_create_jobs_from_request.assert_called_once_with("test1", operator1.id, str(job_group.id), notify=False)

        # Test finding single operator in request_callback via fastq_metadata
        operators = fetch_operators_wfastq(file_metadata.metadata)
        self.assertEqual(operators[0].id, 11)
        self.assertEquals(operators[0].slug, "Operator1")

        #  Test finding multiple operator in request_callback via fastq_metadata
        operator2 = Operator.objects.create(
            slug="Operator2",
            class_name="Operator",
            recipes=["TestAssay"],
            recipes_json=[{"genePanel": "TestAssay", "baitSet": "TestBait"}],
            active=True,
        )
        operators = fetch_operators_wfastq(file_metadata.metadata)
        self.assertEqual([op.id for op in operators], [11, 12])
        self.assertEqual([op.slug for op in operators], ["Operator1", "Operator2"])

    @patch("runner.tasks.create_jobs_from_request.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("notifier.tasks.send_notification.delay")
    @patch("beagle_etl.jobs.metadb_jobs.request_update_notification")
    def test_request_callback_two_operators(
        self,
        request_update_notification,
        send_notification,
        populate_job_group_notifier_metadata,
        mock_create_jobs_from_request,
    ):
        request_update_notification.return_value = None
        populate_job_group_notifier_metadata.return_value = True
        send_notification.return_value = True
        job_group = JobGroup.objects.create()
        notifier = Notifier.objects.create(default=False, notifier_type="JIRA", board="IMPORT")
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group, notifier_type=notifier)
        file_conflict = File.objects.create(
            path="/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
            file_type=self.fastq,
            file_group=self.file_group,
        )
        date_now = date.today().strftime("%Y-%m-%d")
        file_metadata = FileMetadata.objects.create_or_update(
            file=file_conflict,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: "test1",
                "genePanel": "TestAssay",
                "labHeadEmail": "test@email.com",
                "runDate": date_now,
            },
        )
        operator1 = Operator.objects.create(
            slug="Operator1",
            class_name="Operator",
            recipes=["TestAssay"],
            recipes_json=[{"genePanel": "TestAssay"}],
            active=True,
        )
        operator2 = Operator.objects.create(
            slug="Operator2",
            class_name="Operator",
            recipes=["TestAssay"],
            recipes_json=[{"genePanel": "TestAssay"}],
            active=True,
        )
        request_callback(
            "test1",
            "TestAssay",
            file_metadata.metadata,
            [],
            job_group_id=str(job_group.id),
            job_group_notifier_id=str(job_group_notifier.id),
        )

        calls = [
            call("test1", operator1.id, str(job_group.id), notify=False),
            call("test1", operator2.id, str(job_group.id), notify=False),
        ]

        mock_create_jobs_from_request.assert_has_calls(calls, any_order=True)

    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.request_update_notification")
    def test_request_callback_unknown_assay(
        self, request_update_notification, populate_job_group_notifier_metadata, mock_send_notification
    ):
        request_update_notification.return_value = None
        populate_job_group_notifier_metadata.return_value = True
        job_group = JobGroup.objects.create()
        notifier = Notifier.objects.create(default=False, notifier_type="JIRA", board="IMPORT")
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group, notifier_type=notifier)
        file_conflict = File.objects.create(
            path="/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
            file_type=self.fastq,
            file_group=self.file_group,
        )
        file_metadata = FileMetadata.objects.create_or_update(
            file=file_conflict,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: "test1",
                "recipe": "UnknownAssay",
                "labHeadEmail": "test@email.com",
            },
        )
        request_callback(
            "test1", "UnknownAssay", file_metadata.metadata, [], str(job_group.id), str(job_group_notifier.id)
        )

        calls = [
            call({"class": "SetCIReviewEvent", "job_notifier": str(job_group_notifier.id)}),
            call({"class": "SetLabelEvent", "job_notifier": str(job_group_notifier.id), "label": "unrecognized_assay"}),
            call({"class": "UnknownAssayEvent", "job_notifier": str(job_group_notifier.id), "assay": "UnknownAssay"}),
        ]

        mock_send_notification.assert_has_calls(calls, any_order=True)

    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.request_update_notification")
    def test_request_callback_disabled_assay(
        self, request_update_notification, populate_job_group_notifier_metadata, mock_send_notification
    ):
        request_update_notification.return_value = None
        populate_job_group_notifier_metadata.return_value = True
        job_group = JobGroup.objects.create()
        notifier = Notifier.objects.create(default=False, notifier_type="JIRA", board="IMPORT")
        job_group_notifier = JobGroupNotifier.objects.create(job_group=job_group, notifier_type=notifier)
        file_conflict = File.objects.create(
            path="/path/to/sample/08/sampleName_002-d_IGO_igoId_002_S134_L008_R2_001.fastq.gz",
            file_type=self.fastq,
            file_group=self.file_group,
        )
        file_metadata = FileMetadata.objects.create_or_update(
            file=file_conflict,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: "test1",
                "recipe": "DisabledAssay1",
                "labHeadEmail": "test@email.com",
            },
        )
        request_callback(
            "test1", "DisabledAssay1", file_metadata.metadata, [], str(job_group.id), str(job_group_notifier.id)
        )

        calls = [
            call({"class": "NotForCIReviewEvent", "job_notifier": str(job_group_notifier.id)}),
            call(
                {"class": "DisabledAssayEvent", "job_notifier": str(job_group_notifier.id), "assay": "DisabledAssay1"}
            ),
        ]

        mock_send_notification.assert_has_calls(calls, any_order=True)
