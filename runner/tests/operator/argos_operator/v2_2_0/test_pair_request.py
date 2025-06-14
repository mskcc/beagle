import json
import os
from uuid import UUID

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from file_system.models import File, FileGroup, FileMetadata, FileType
from runner.operator.argos_operator.v2_2_0.bin.pair_request import compile_pairs

"""
Order of smart pairing
Given a single tumor sample, find
1. a normal sample that belongs to the same patient. This should be first from the same request, then should search across other requests and projects. We can get help from the IGO PMs on which other requests/projects should be searched for a custom request.
2. a dmp normal bam to be pulled in for that patient if it exists.
3. a closest related normal. (No code written yet)
4. the appropriate pooled normal. This will be frozen or FFPE depending on the data_clinical information for that sample, and need to parse by assay used (impact/hemepact).
"""


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


class TestPairRequest(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

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
        file_group_id = UUID("1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
        file_group_instance = FileGroup.objects.get(id=file_group_id)
        filetype_instance = FileType.objects.get(id=1, name="fastq")

        # make demo file entry
        file_instance = File.objects.create(
            file_group=file_group_instance, file_type=filetype_instance, file_name="foo"
        )

        FileMetadata.objects.create_or_update(file=file_instance, metadata={})

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
        expected_pairs = {"tumor": [], "normal": []}
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs1(self):
        """
        Test pairing with a single pair of samples
        """
        samples = [
            {
                "patient_id": "C-W86LMR",
                "bait_set": "IMPACT468_BAITS",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "sample_id": "my_sample_id2",
                "SM": "my_sample_id2",
                "run_mode": "HiSeq High Output",
            },
            {
                "patient_id": "C-W86LMR",
                "bait_set": "IMPACT468_BAITS",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id1",
                "sample_id": "my_sample_id1",
                "run_mode": "HiSeq High Output",
            },
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "patient_id": "C-W86LMR",
                    "bait_set": "IMPACT468_BAITS",
                    "tumor_type": "Tumor",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id1",
                    "SM": "my_sample_id1",
                    "run_mode": "HiSeq High Output",
                }
            ],
            "normal": [
                {
                    "patient_id": "C-W86LMR",
                    "bait_set": "IMPACT468_BAITS",
                    "tumor_type": "Normal",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id2",
                    "SM": "my_sample_id2",
                    "run_mode": "HiSeq High Output",
                }
            ],
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
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "SM": "my_sample_id1",
                "sample_id": "my_sample_id1",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-8VK0V7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "SM": "my_sample_id2",
                "sample_id": "my_sample_id2",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-DRKHP7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id3",
                "sample_id": "my_sample_id3",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-8VK0V7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id4",
                "sample_id": "my_sample_id4",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-DRKHP7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id5",
                "sample_id": "my_sample_id5",
                "run_mode": "HiSeq High Output",
            },
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-DRKHP7",
                    "tumor_type": "Tumor",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id3",
                    "SM": "my_sample_id3",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-8VK0V7",
                    "tumor_type": "Tumor",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id4",
                    "SM": "my_sample_id4",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-DRKHP7",
                    "tumor_type": "Tumor",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id5",
                    "SM": "my_sample_id5",
                    "run_mode": "HiSeq High Output",
                },
            ],
            "normal": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-DRKHP7",
                    "tumor_type": "Normal",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id1",
                    "SM": "my_sample_id1",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-8VK0V7",
                    "tumor_type": "Normal",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id2",
                    "SM": "my_sample_id2",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-DRKHP7",
                    "tumor_type": "Normal",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id1",
                    "SM": "my_sample_id1",
                    "run_mode": "HiSeq High Output",
                },
            ],
        }

        print("Running test_compile_pairs2 ---")
        print(json.dumps(pairs, cls=UUIDEncoder))
        print(json.dumps(expected_pairs, cls=UUIDEncoder))

        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs3(self):
        """
        Test pairing with only a single Normal sample
        """
        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-DRKHP7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "run_mode": "HiSeq High Output",
            }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {"tumor": [], "normal": []}
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs4(self):
        """
        Test pairing with only a single unpaired Tumor sample
        Test that the appropriate Normal sample is found from the other samples in the same request
        missing normal for sample 10075_D_1; querying patient C-DRKHP7
        """
        # Load fixtures:
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-DRKHP7",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "10075_D_1",
                "sample_id": "10075_D_1",
                "run_mode": "hiseq",
            }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "normal": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_C_DRKHP7_N001_d_HCYYWBBXY"],
                    "LB": "10075_D_2",
                    "PL": "Illumina",
                    "PU": ["HCYYWBBXY"],
                    "R1": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("aef306b4-7d85-4c9f-b9a4-a115154f73bf")],
                    "R2": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("9e47ba2f-093a-4233-8339-fed03e159b3f")],
                    "bam": [],
                    "bam_bid": [],
                    "SM": "s_C_DRKHP7_N001_d",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_2",
                    "patient_id": "C-DRKHP7",
                    "request_id": "10075_D",
                    "run_id": ["JAX_0397"],
                    "run_mode": "hiseq",
                    "preservation_type": ["Frozen"],
                    "run_date": ["2019-12-12"],
                    "species": "Human",
                    "specimen_type": "Blood",
                    "tumor_type": "Normal",
                    "pi": "John Smith",
                    "pi_email": "email@internet.com",
                }
            ],
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_1",
                    "SM": "10075_D_1",
                    "patient_id": "C-DRKHP7",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "tumor_type": "Tumor",
                    "run_mode": "hiseq",
                }
            ],
        }

        print("Running test_compile_pairs4 ----")
        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs5(self):
        """
        Test pairing with a single unpaired tumor sample
        Test that the correct Normal sample is found from within the same request
        This time also load File entries from another request to make sure they do not confound the pairing
        """
        # Load fixtures
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D.filemetadata.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "05257_CB.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "05257_CB.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 14)
        self.assertTrue(len(FileMetadata.objects.all()) == 18)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-DRKHP7",
                "tumor_type": "Tumor",
                "run_id": ["JAX_0397"],
                "preservation_type": ["Frozen"],
                "SM": "10075_D_1",
                "sample_id": "10075_D_1",
                "run_mode": "hiseq",
            }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "normal": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_C_DRKHP7_N001_d_HCYYWBBXY"],
                    "LB": "10075_D_2",
                    "PL": "Illumina",
                    "PU": ["HCYYWBBXY"],
                    "R1": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("aef306b47d854c9fb9a4a115154f73bf")],
                    "R2": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D/Sample_31-N_IGO_10075_D_2/31-N_IGO_10075_D_2_S14_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("9e47ba2f093a42338339fed03e159b3f")],
                    "bam": [],
                    "bam_bid": [],
                    "SM": "s_C_DRKHP7_N001_d",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_2",
                    "patient_id": "C-DRKHP7",
                    "request_id": "10075_D",
                    "run_id": ["JAX_0397"],
                    "run_mode": "hiseq",
                    "preservation_type": ["Frozen"],
                    "run_date": ["2019-12-12"],
                    "species": "Human",
                    "specimen_type": "Blood",
                    "tumor_type": "Normal",
                    "pi": "John Smith",
                    "pi_email": "email@internet.com",
                }
            ],
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_1",
                    "SM": "10075_D_1",
                    "patient_id": "C-DRKHP7",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["Frozen"],
                    "tumor_type": "Tumor",
                    "run_mode": "hiseq",
                }
            ],
        }

        self.assertTrue(pairs == expected_pairs)

    def test_get_pair_from_other_request(self):
        """
        Test that you can get the correct Normal sample for a patient when the
        Normal sample is part of another request
        """
        # Load fixtures
        # only normals
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.filemetadata.json"), verbosity=0)
        # only tumors
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_3.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_3.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 4)
        self.assertTrue(len(FileMetadata.objects.all()) == 4)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-8VK0V7",
                "tumor_type": "Tumor",
                "run_id": ["JAX_0397"],
                "preservation_type": ["EDTA-Streck"],
                "sample_id": "10075_D_3_5",
                "SM": "10075_D_3_5",
                "request_id": "10075_D_3",
                "run_mode": "hiseq",
            }
        ]

        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-8VK0V7",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["EDTA-Streck"],
                    "tumor_type": "Tumor",
                    "sample_id": "10075_D_3_5",
                    "SM": "10075_D_3_5",
                    "request_id": "10075_D_3",
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["HCYYWBBXY"],
                    "LB": "10075_D_2_3",
                    "tumor_type": "Normal",
                    "ID": ["s_C_8VK0V7_N001_d_HCYYWBBXY"],
                    "SM": "s_C_8VK0V7_N001_d",
                    "species": "Human",
                    "patient_id": "C-8VK0V7",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_2_3",
                    "run_date": ["2019-12-12"],
                    "specimen_type": "Blood",
                    "R1": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz"
                    ],
                    "R2": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("7a3bceb31af84d3da1583731c83aeb5a")],
                    "R2_bid": [UUID("ecf003cdbd304e909d180d99e7fd79d3")],
                    "bam": [],
                    "bam_bid": [],
                    "request_id": "10075_D_2",
                    "run_id": ["JAX_0397"],
                    "run_mode": "hiseq",
                    "preservation_type": ["EDTA-Streck"],
                    "pi": "John Smith",
                    "pi_email": "email@internet.com",
                }
            ],
        }

        self.assertTrue(pairs == expected_pairs)

    def test_get_most_recent_normal1(self):
        """
        Test that when retreiving a normal from other requests, the most recent Normal is returned
        in the event that a patient has several normals
        Return the Normal with the most recent run_date
        """
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.filemetadata.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_4.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_4.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 4)
        self.assertTrue(len(FileMetadata.objects.all()) == 4)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-8VK0V7",
                "tumor_type": "Tumor",
                "sample_id": "10075_D_3_5",
                "SM": "10075_D_3_5",
                "request_id": "10075_D_3",
                "run_id": ["JAX_0397"],
                "preservation_type": ["EDTA-Streck"],
                "run_mode": "hiseq",
            }
        ]

        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-8VK0V7",
                    "tumor_type": "Tumor",
                    "sample_id": "10075_D_3_5",
                    "SM": "10075_D_3_5",
                    "request_id": "10075_D_3",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["EDTA-Streck"],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["HCYYWBBXY"],
                    "LB": "10075_D_4_3",
                    "tumor_type": "Normal",
                    "ID": ["s_C_8VK0V7_N001_d_HCYYWBBXY"],
                    "SM": "s_C_8VK0V7_N001_d",
                    "species": "Human",
                    "patient_id": "C-8VK0V7",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "10075_D_4_3",
                    "run_date": ["2019-12-13"],
                    "specimen_type": "Blood",
                    "R1": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_4/Sample_JW_MEL_007_NORM_IGO_10075_D_4_3/JW_MEL_007_NORM_IGO_10075_D_4_3_S15_R1_001.fastq.gz"
                    ],
                    "R2": [
                        "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_4/Sample_JW_MEL_007_NORM_IGO_10075_D_4_3/JW_MEL_007_NORM_IGO_10075_D_4_3_S15_R2_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("404ad544428c405f967aa6920d091148")],
                    "R2_bid": [UUID("19703ff82e144f608d57891df80b2858")],
                    "bam": [],
                    "bam_bid": [],
                    "request_id": "10075_D_4",
                    "run_id": ["JAX_0397"],
                    "preservation_type": ["EDTA-Streck"],
                    "pi": "John Smith",
                    "pi_email": "email@internet.com",
                    "run_mode": "hiseq",
                }
            ],
        }

        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs_custom1(self):
        """
        Test the ability to compile pairs with a custom sample set

        TODO: what pair attributes is this testing?
        """
        samples = [
            {
                "CN": "MSKCC",
                "ID": ["s_juno_argos_demo1_3_HCYYWBBXY"],
                "LB": "juno_argos_demo1_3",
                "PL": "Illumina",
                "PU": ["HCYYWBBXY"],
                "R1": ["/juno/work/ci/argos-test/data/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                "R1_bid": [UUID("a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac")],
                "R2": ["/juno/work/ci/argos-test/data/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                "R2_bid": [UUID("c71c259a-ebc0-4490-9af1-bc99387a70d7")],
                "bam": [],
                "bam_bid": [],
                "SM": "s_juno_argos_demo1_3",
                "bait_set": "IMPACT468_BAITS",
                "sample_id": "s_juno_argos_demo1_3",
                "patient_id": "DU874145",
                "request_id": "juno_argos_demo1",
                "run_id": ["JAX_0397"],
                "preservation_type": ["EDTA-Streck"],
                "run_date": ["2019-12-12"],
                "species": "Human",
                "specimen_type": "Blood",
                "tumor_type": "Normal",
                "run_mode": "hiseq",
            },
            {
                "CN": "MSKCC",
                "ID": ["s_juno_argos_demo1_5_HFTCNBBXY_GTATTGGC-TTGTCGGT"],
                "LB": "juno_argos_demo1_5_1_1_1",
                "PL": "Illumina",
                "PU": ["HFTCNBBXY_GTATTGGC-TTGTCGGT"],
                "R1": ["/juno/work/ci/argos-test/data/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                "R1_bid": [UUID("d2d8ed36-d8f4-4e93-b038-d38328fad021")],
                "R2": ["/juno/work/ci/argos-test/data/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                "R2_bid": [UUID("2f77f3ac-ab25-4a02-90bd-86542401ac89")],
                "bam": [],
                "bam_bid": [],
                "SM": "s_juno_argos_demo1_5",
                "bait_set": "IMPACT468_BAITS",
                "sample_id": "s_juno_argos_demo1_5",
                "patient_id": "DU874145",
                "request_id": "juno_argos_demo1",
                "run_id": ["JAX_0397"],
                "preservation_type": ["EDTA-Streck"],
                "run_date": ["2019-12-17"],
                "species": "Human",
                "specimen_type": "Resection",
                "tumor_type": "Tumor",
                "run_mode": "hiseq",
            },
        ]
        pairs = compile_pairs(samples)

        expected_pairs = {
            "tumor": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_juno_argos_demo1_5_HFTCNBBXY_GTATTGGC-TTGTCGGT"],
                    "LB": "juno_argos_demo1_5_1_1_1",
                    "PL": "Illumina",
                    "PU": ["HFTCNBBXY_GTATTGGC-TTGTCGGT"],
                    "R1": [
                        "/juno/work/ci/argos-test/data/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("d2d8ed36-d8f4-4e93-b038-d38328fad021")],
                    "R2": [
                        "/juno/work/ci/argos-test/data/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("2f77f3ac-ab25-4a02-90bd-86542401ac89")],
                    "SM": "s_juno_argos_demo1_5",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "s_juno_argos_demo1_5",
                    "patient_id": "DU874145",
                    "request_id": "juno_argos_demo1",
                    "run_id": ["JAX_0397"],
                    "run_date": ["2019-12-17"],
                    "species": "Human",
                    "specimen_type": "Resection",
                    "tumor_type": "Tumor",
                    "preservation_type": ["EDTA-Streck"],
                    "bam": [],
                    "bam_bid": [],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_juno_argos_demo1_3_HCYYWBBXY"],
                    "LB": "juno_argos_demo1_3",
                    "PL": "Illumina",
                    "PU": ["HCYYWBBXY"],
                    "R1": [
                        "/juno/work/ci/argos-test/data/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac")],
                    "R2": [
                        "/juno/work/ci/argos-test/data/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("c71c259a-ebc0-4490-9af1-bc99387a70d7")],
                    "SM": "s_juno_argos_demo1_3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "s_juno_argos_demo1_3",
                    "patient_id": "DU874145",
                    "request_id": "juno_argos_demo1",
                    "run_id": ["JAX_0397"],
                    "run_date": ["2019-12-12"],
                    "species": "Human",
                    "specimen_type": "Blood",
                    "tumor_type": "Normal",
                    "preservation_type": ["EDTA-Streck"],
                    "bam": [],
                    "bam_bid": [],
                    "run_mode": "hiseq",
                }
            ],
        }

        print("Running test_compile_pairs_custom1 ----")
        print(json.dumps(pairs, cls=UUIDEncoder))
        print(json.dumps(expected_pairs, cls=UUIDEncoder))

        self.assertTrue(pairs == expected_pairs)
