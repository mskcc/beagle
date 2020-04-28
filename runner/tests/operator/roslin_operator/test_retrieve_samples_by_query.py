import os
from uuid import UUID
from django.test import TestCase
from django.db.models import Prefetch, Q
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import build_dmp_query
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import get_dmp_normal
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import get_pooled_normals
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import build_run_id_query
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import build_preservation_query
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import get_descriptor
from django.conf import settings
from django.core.management import call_command
from file_system.models import File, FileMetadata, FileGroup, FileType

class TestRetrieveSamplesByQuery(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def test_build_dmp_query1(self):
        """
        Test that DMP query is built correctly given different input parameters
        """
        # with dummy values
        patient_id = "foo"
        bait_set = "bar"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='') & Q(filemetadata__metadata__patient__cmo='foo') & Q(filemetadata__metadata__type='N')
        # (AND: ('filemetadata__metadata__cmo_assay', ''), ('filemetadata__metadata__patient__cmo', 'foo'), ('filemetadata__metadata__type', 'N'))
        self.assertEqual(dmp_query, expected_query)

        # with dummy CMO-ID style patient ID
        patient_id = "C-foo"
        bait_set = "bar"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='') & Q(filemetadata__metadata__patient__cmo='foo') & Q(filemetadata__metadata__type='N')
        self.assertEqual(dmp_query, expected_query)

        # dummy CMO-ID style patient ID and partially matching bait_set impact341
        patient_id = "C-foo1"
        bait_set = "IMPACT341_foo"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='IMPACT341') & Q(filemetadata__metadata__patient__cmo='foo1') & Q(filemetadata__metadata__type='N')
        self.assertEqual(dmp_query, expected_query)

    def test_get_dmp_normal1(self):
        """
        Test retrieval of a DMP Normal .bam for a given CMO Patient ID
        """
        # test lookup with no loaded DMP bams, no matches
        patient_id = "foo"
        bait_set = "bar"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # load some fixtures
        # Load fixtures:
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.file.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.filemetadata.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        # test lookup again with some Files loaded; should still be None since it doesnt match anything yet
        patient_id = "foo"
        bait_set = "bar"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # test with a patient ID taken from fixtures but non-matching bait set; no DMP bams loaded yet
        patient_id = "C-8VK0V7"
        bait_set = "bar"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # test with a patient ID taken from fixtures and matching bait_set; no DMP bams loaded yet
        patient_id = "C-8VK0V7"
        bait_set = "IMPACT468_BAITS"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # create a DMP bam
        file_group_instance = FileGroup.objects.get(name = "DMP BAMs")
        filetype_instance = FileType.objects.get(name = "bam")
        file_instance = File.objects.create(
            file_type = filetype_instance,
            file_group = file_group_instance,
            file_name = "C-8VK0V7.bam",
            path = "/C-8VK0V7.bam"
        )
        dmp_bam_filemetadata_instance = FileMetadata.objects.create(
            file = file_instance,
            version = 1,
            metadata = {
                "bai": "/C-8VK0V7.bai",
                "bam": "/C-8VK0V7.bam",
                "type": "N",
                "assay": "IM6",
                "sample": "P-1234567-N01-IM6",
                "anon_id": "ABCDEF-N",
                "patient": {
                    "cmo": "8VK0V7",
                    "dmp": "P-1234567",
                    "updated": "2020-03-19T23:57:51.941963Z",
                    "imported": "2020-03-19T23:57:51.941945Z"},
                "updated": "2020-03-25T19:45:16.421154Z",
                "version": 1,
                "coverage": 648,
                "imported": "2020-03-25T19:45:16.421137Z",
                "cmo_assay": "IMPACT468",
                "tumor_type": "MBC",
                "external_id": "C-8VK0V7-N901-dZ-IM6",
                "sample_type": "0",
                "tissue_type": "Breast",
                "primary_site": "Breast",
                "project_name": "UK12344567890VB",
                "patient_group": "Group_12344567890",
                "part_c_consent": 1,
                "metastasis_site": "Not Applicable",
                "somatic_calling_status": "Matched",
                "major_allele_contamination": 0.452,
                "minor_allele_contamination": 0.00069
            }
        )

        # test with a patient ID taken from fixtures but non-matching bait_set
        patient_id = "C-8VK0V7"
        bait_set = "foo"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # test with a non-matching patient ID and a matching bait_set
        patient_id = "foo"
        bait_set = "IMPACT468_BAITS"
        dmp_normal = get_dmp_normal(patient_id, bait_set)
        self.assertEqual(dmp_normal, None)

        # test with a patient ID taken from fixtures and a matching bait_set
        patient_id = "C-8VK0V7"
        bait_set = "IMPACT468_BAITS"
        dmp_normal = get_dmp_normal(patient_id, bait_set)

        expected_dmp_normal = {
            'CN': 'MSKCC',
            'PL': 'Illumina',
            'PU': ['DMP_FCID_DMP_BARCODEIDX'],
            'LB': 'C-8VK0V7-N901-dZ-IM6_1',
            'tumor_type': 'Normal',
            'ID': ['C-8VK0V7-N901-dZ-IM6_DMP_FCID_DMP_BARCODEIDX'],
            'SM': 'C-8VK0V7-N901-dZ-IM6',
            'species': '',
            'patient_id': 'C-8VK0V7',
            'bait_set': 'IMPACT468_BAITS',
            'sample_id': 'C-8VK0V7-N901-dZ-IM6',
            'run_date': [''],
            'specimen_type': '',
            'R1': [],
            'R2': [],
            'R1_bid': [],
            'R2_bid': [],
            'bam': ['/C-8VK0V7.bam'],
            'bam_bid': [
                # mock the UUID for testing since it will be different every time
                "deletemeplease"
                ],
            'request_id': 'C-8VK0V7-N901-dZ-IM6',
            'pi': '',
            'pi_email': '',
            'run_id': [''],
            'preservation_type': ['']
        }

        # remove the bam_bid UUID value for testing because it will be different every time
        # TODO: patch or mock this
        dmp_normal.pop('bam_bid')
        expected_dmp_normal.pop('bam_bid')

        self.assertEqual(dmp_normal, expected_dmp_normal)

    def test_build_run_id_query(self):
        """
        Test that a run id query is built correctly
        """
        run_ids = ['bar']
        query = build_run_id_query(run_ids)
        # (AND: (('filemetadata__metadata__runId', 'bar'))
        expected_query = Q(filemetadata__metadata__runId='bar')
        self.assertEqual(query, expected_query)

        # run them through set then back to list to ensure ordering for testing
        run_ids = set(['bar', 'baz'])
        query = build_run_id_query(run_ids)
        # query.__dict__
        # {'children': [('filemetadata__metadata__runId', 'baz'), ('filemetadata__metadata__runId', 'bar')], 'connector': 'OR', 'negated': False}

        # order not guaranteed due to usage of set inside build_run_id_query
        expected_query = Q(filemetadata__metadata__runId='bar') | Q(filemetadata__metadata__runId='baz')
        # (OR: ('filemetadata__metadata__runId', 'baz'), ('filemetadata__metadata__runId', 'bar'))

        self.assertTrue( ('filemetadata__metadata__runId', 'baz') in query.__dict__['children'] )
        self.assertTrue( ('filemetadata__metadata__runId', 'bar') in query.__dict__['children'] )
        self.assertTrue( query.__dict__['connector'] == 'OR' )
        self.assertTrue( query.__dict__['negated'] == False )


    def test_build_preservation_query(self):
        """
        Test that a preservation type query is built correctly
        Test different combinations of valid and invalid preservation types, with and without caps
        """
        preservation_types = list(set(['foo', 'bar']))
        query = build_preservation_query(preservation_types)
        # TODO: why does this give the preservation type of "FROZEN"?
        expected_query = Q(filemetadata__metadata__preservation__iexact='FROZEN')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['foo', 'frozen']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FROZEN')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['foo', 'ffpe']))
        query = build_preservation_query(preservation_types)
        # TODO: why does this give the preservation type of "FFPE"?
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['foo', 'FFPE']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['frozen', 'ffpe']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['frozen', 'FFPE']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['FROZEN', 'ffpe']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['FROZEN', 'FFPE']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['FFPE']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['ffpe']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FFPE')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['frozen']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FROZEN')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['Frozen']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FROZEN')
        self.assertEqual(query, expected_query)

        preservation_types = list(set(['FROZEN']))
        query = build_preservation_query(preservation_types)
        expected_query = Q(filemetadata__metadata__preservation__iexact='FROZEN')
        self.assertEqual(query, expected_query)

    def test_get_descriptor1(self):
        """
        Test that re-labeled descriptor is returned when needed
        """
        # create some Pooled Normals
        poolednormal_filegroup_instance = FileGroup.objects.get(name = "Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name = "fastq")
        poolednormal_R1_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R1.fastq",
            path = "/FROZENPOOLEDNORMAL.R1.fastq"
        )
        poolednormal_R1_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R1_file_instance,
            metadata = {
                "recipe": "IMPACT468",
            }
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R2.fastq",
            path = "/FROZENPOOLEDNORMAL.R2.fastq"
        )
        poolednormal_R2_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R2_file_instance,
            metadata = {
                "recipe": "IMPACT468",
            }
        )
        pooled_normals = File.objects.all()

        descriptor = get_descriptor(bait_set = "IMPACT468_BAITS", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, "IMPACT468")

        descriptor = get_descriptor(bait_set = "IMPACT468", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, "IMPACT468")

    def test_get_descriptor2(self):
        """
        Test that no descriptor is returned when its not needed
        """
        # create some Pooled Normals
        poolednormal_filegroup_instance = FileGroup.objects.get(name = "Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name = "fastq")
        poolednormal_R1_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R1.fastq",
            path = "/FROZENPOOLEDNORMAL.R1.fastq"
        )
        poolednormal_R1_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R1_file_instance,
            metadata = {
                "recipe": "foo_IMPACT468_bar",
            }
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R2.fastq",
            path = "/FROZENPOOLEDNORMAL.R2.fastq"
        )
        poolednormal_R2_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R2_file_instance,
            metadata = {
                "recipe": "foo_IMPACT468_bar",
            }
        )
        pooled_normals = File.objects.all()

        descriptor = get_descriptor(bait_set = "IMPACT468", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, None)

        descriptor = get_descriptor(bait_set = "IMPACT468_bar", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, None)

        descriptor = get_descriptor(bait_set = "foo_IMPACT468", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, None)

        descriptor = get_descriptor(bait_set = "foo_IMPACT468_bar", pooled_normals = pooled_normals)
        self.assertEqual(descriptor, "foo_IMPACT468_bar")

    def test_get_pooled_normals1(self):
        """
        Test that Pooled Normals can be retrived correctly
        """
        # test that an empty database and irrelevant args returns None
        pooled_normals = get_pooled_normals(
            run_ids = ['foo'], preservation_types = ['bar'], bait_set = "baz"
        )
        self.assertEqual(pooled_normals, None)

        # start adding Pooled Normals to the database
        poolednormal_filegroup_instance = FileGroup.objects.get(name = "Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name = "fastq")
        # add Pooled Normal from another run
        poolednormal_R1_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R1.fastq",
            path = "/FROZENPOOLEDNORMAL.R1.fastq"
        )
        poolednormal_R1_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R1_file_instance,
            metadata = {
                "runId": "PITT_0439",
                "recipe": "IMPACT468",
                'baitSet': 'IMPACT468_BAITS',
                "preservation": "Frozen"
            }
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type = fastq_filetype_instance,
            file_group = poolednormal_filegroup_instance,
            file_name = "FROZENPOOLEDNORMAL.R2.fastq",
            path = "/FROZENPOOLEDNORMAL.R2.fastq"
        )
        poolednormal_R2_filemetadata_instance = FileMetadata.objects.create(
            file = poolednormal_R2_file_instance,
            metadata = {
                "runId": "PITT_0439",
                "recipe": "IMPACT468",
                'baitSet': 'IMPACT468_BAITS',
                "preservation": "Frozen"
            }
        )

        pooled_normals = get_pooled_normals(
            run_ids = ['PITT_0439'],
            preservation_types = ['Frozen'],
            bait_set = "IMPACT468_BAITS"
        )
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pooled_normals['R1_bid'].pop()
        pooled_normals['R2_bid'].pop()

        expected_pooled_normals = {
        'CN': 'MSKCC',
        'PL': 'Illumina',
        'PU': ['PN_FCID_FROZENPOOLEDNORMAL'],
        'LB': 'pooled_normal_IMPACT468_PITT_0439_Frozen_1',
        'tumor_type': 'Normal',
        'ID': ['pooled_normal_IMPACT468_PITT_0439_Frozen_PN_FCID_FROZENPOOLEDNORMAL'],
        'SM': 'pooled_normal_IMPACT468_PITT_0439_Frozen',
        'species': '',
        'patient_id': 'PN_PATIENT_ID',
        'bait_set': 'IMPACT468',
        'sample_id': 'pooled_normal_IMPACT468_PITT_0439_Frozen',
        'run_date': [''],
        'specimen_type': '',
        'R1': ['/FROZENPOOLEDNORMAL.R1.fastq'],
        'R2': ['/FROZENPOOLEDNORMAL.R2.fastq'],
        'R1_bid': [], # UUID('7268ac6e-e9a6-48e0-94f1-1c894280479b')
        'R2_bid': [], # UUID('ec9817d1-d6f5-4f1d-9c0a-c82fc22d4daa')
        'bam': [],
        'bam_bid': [],
        'request_id': 'pooled_normal_IMPACT468_PITT_0439_Frozen',
        'pi': '',
        'pi_email': '',
        'run_id': [''],
        'preservation_type': [['Frozen']]
        }

        self.assertEqual(pooled_normals, expected_pooled_normals)
