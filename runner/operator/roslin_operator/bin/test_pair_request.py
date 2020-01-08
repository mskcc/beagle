import os
from uuid import UUID
from django.test import TestCase
from .pair_request import compile_pairs
from file_system.models import File, FileMetadata, FileGroup, FileType
from django.conf import settings
from django.core.management import call_command
"""
Order of smart pairing
Given a single tumor sample, find
1. a normal sample that belongs to the same patient. This should be first from the same request, then should search across other requests and projects. We can get help from the IGO PMs on which other requests/projects should be searched for a custom request.
2. a dmp normal bam to be pulled in for that patient if it exists. (Need to modify existing code)
3. a closest related normal. (No code written yet)
4. the appropriate pooled normal. This will be frozen or FFPE depending on the data_clinical information for that sample, and need to parse by assay used (impact/hemepact).
"""

class TestPairRequest(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def test_true(self):
        self.assertTrue(True)

    def test_validate_test_db_files(self):
        """
        Sanity check
        Need to make sure that the test db has no file or file metadata entries
        to ensure test results are consistent and we are not accidentally pulling
        in unintended files when testing
        """
        files = File.objects.all()
        filesMetadata = FileMetadata.objects.all()
        self.assertTrue(len(files) == 0)
        self.assertTrue(len(filesMetadata) == 0)

    def test_validate_load_files(self):
        """
        Sanity check
        Check to make sure that we can load a single File into the test db
        And that only one file is present in the db after loading
        """
        # loaded from static repo fixtures
        file_group_id = UUID('1a1b29cf-3bc2-4f6c-b376-d4c5d701166a')
        file_group_instance = FileGroup.objects.get(id = file_group_id)
        filetype_instance = FileType.objects.get(id = 1, ext = "fastq")

        # make demo file entry
        file_instance = File.objects.create(
        file_group = file_group_instance,
        file_type = filetype_instance,
        file_name = "foo"
        )

        file_metadata_instance = FileMetadata.objects.create(
        file = file_instance,
        metadata = '{}'
        )

        # check that only one file entry exists in the test db
        files = File.objects.all()
        file_metadatas = FileMetadata.objects.all()
        self.assertTrue(len(files) == 1)
        self.assertTrue(len(file_metadatas) == 1)

    def test_compile_pairs0(self):
        """
        Test the results of pairing with no tumor or normal samples; should give empty output
        """
        samples = []
        pairs = compile_pairs(samples)
        expected_pairs = {'tumor': [], 'normal': []}
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs1(self):
        """
        Test pairing with a single pair of samples
        """
        samples = [
        {
        "patient_id": "C-W86LMR",
        "bait_set": "IMPACT468_BAITS",
        "tumor_type": "Normal"
        },
        {
        "patient_id": "C-W86LMR",
        "bait_set": "IMPACT468_BAITS",
        "tumor_type": "Tumor"
        }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
        'tumor': [
        {'patient_id': 'C-W86LMR', 'bait_set': 'IMPACT468_BAITS', 'tumor_type': 'Tumor'}
        ],
        'normal': [
        {'patient_id': 'C-W86LMR', 'bait_set': 'IMPACT468_BAITS', 'tumor_type': 'Normal'}
        ]
        }
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs2(self):
        """
        Test pairing with multiple samples in a request
        """
        samples = [
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-DRKHP7",
        "tumor_type": "Normal"
        },
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-8VK0V7",
        "tumor_type": "Normal"
        },
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-DRKHP7",
        "tumor_type": "Tumor"
        },
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-8VK0V7",
        "tumor_type": "Tumor"
        },
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-DRKHP7",
        "tumor_type": "Tumor"
        }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
        'tumor': [
        {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-DRKHP7', 'tumor_type': 'Tumor'}, {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-8VK0V7', 'tumor_type': 'Tumor'}, {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-DRKHP7', 'tumor_type': 'Tumor'}
        ],
        'normal': [
        {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-DRKHP7', 'tumor_type': 'Normal'}, {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-8VK0V7', 'tumor_type': 'Normal'}, {'bait_set': 'IMPACT468_BAITS', 'patient_id': 'C-DRKHP7', 'tumor_type': 'Normal'}
        ]
        }
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs3(self):
        """
        Test pairing with only a single Normal sample
        """
        samples = [
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-DRKHP7",
        "tumor_type": "Normal"
        }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {'tumor': [], 'normal': []}
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs4(self):
        """
        Test pairing with only a single unpaired Tumor sample
        Test that the appropriate Normal sample is found from the other samples in the same request
        missing normal for sample 10075_D_1; querying patient C-DRKHP7
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.file.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.filemetadata.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        samples = [
        {
        "bait_set": "IMPACT468_BAITS",
        "patient_id": "C-DRKHP7",
        "tumor_type": "Tumor",
        "igo_id": "10075_D_1"
        }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
        'normal': [{
            'CN': 'MSKCC',
            'ID': ['s_C_DRKHP7_N001_d_HCYYWBBXY'],
            'LB': '10075_D_2',
            'PL': 'Illumina',
            'PU': ['HCYYWBBXY'],
            'R1': ['/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R1_001.fastq.gz'],
            'R1_bid': [UUID('40a07e9a-2198-40b7-9f7f-7696c9d6429e')],
            'R2': ['/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R2_001.fastq.gz'],
            'R2_bid': [UUID('bb7ff922-b741-4df7-ba2a-4f3b8549e8b5')],
            'SM': 's_C_DRKHP7_N001_d',
            'bait_set': 'IMPACT468_BAITS',
            'igo_id': '10075_D_2',
            'patient_id': 'C-DRKHP7',
            'request_id': ['10075_D'],
            'run_date': ['2019-12-12'],
            'species': 'Human',
            'specimen_type': 'Blood',
            'tumor_type': 'Normal'
            }],
        'tumor': [{
            'bait_set': 'IMPACT468_BAITS',
            'igo_id': '10075_D_1',
            'patient_id': 'C-DRKHP7',
            'tumor_type': 'Tumor'
            }]
        }
        self.assertTrue(pairs == expected_pairs)
