import os
from uuid import UUID
from django.test import TestCase
from django.db.models import Prefetch, Q
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import build_dmp_query
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import get_dmp_normal
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
