import os
import json
from uuid import UUID
from django.test import TestCase
from runner.operator.argos_operator.v1_2_0.bin.pair_request import compile_pairs
from file_system.models import File, FileMetadata, FileGroup, FileType
from django.conf import settings
from django.core.management import call_command

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
                "patient_id": "C-PPPP21",
                "bait_set": "IMPACT468_BAITS",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "sample_id": "my_sample_id2",
                "SM": "my_sample_id2",
                "run_mode": "HiSeq High Output",
            },
            {
                "patient_id": "C-PPPP21",
                "bait_set": "IMPACT468_BAITS",
                "run_id": ["SEQRUN_0004"],
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
                    "patient_id": "C-PPPP21",
                    "bait_set": "IMPACT468_BAITS",
                    "tumor_type": "Tumor",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id1",
                    "SM": "my_sample_id1",
                    "run_mode": "HiSeq High Output",
                }
            ],
            "normal": [
                {
                    "patient_id": "C-PPPP21",
                    "bait_set": "IMPACT468_BAITS",
                    "tumor_type": "Normal",
                    "run_id": ["SEQRUN_0004"],
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
                "patient_id": "C-PPPPP7",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "SM": "my_sample_id1",
                "sample_id": "my_sample_id1",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP3",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Normal",
                "SM": "my_sample_id2",
                "sample_id": "my_sample_id2",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP7",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id3",
                "sample_id": "my_sample_id3",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP3",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "my_sample_id4",
                "sample_id": "my_sample_id4",
                "run_mode": "HiSeq High Output",
            },
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP7",
                "run_id": ["SEQRUN_0004"],
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
                    "patient_id": "C-PPPPP7",
                    "tumor_type": "Tumor",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id3",
                    "SM": "my_sample_id3",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Tumor",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id4",
                    "SM": "my_sample_id4",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP7",
                    "tumor_type": "Tumor",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id5",
                    "SM": "my_sample_id5",
                    "run_mode": "HiSeq High Output",
                },
            ],
            "normal": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP7",
                    "tumor_type": "Normal",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id1",
                    "SM": "my_sample_id1",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Normal",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["Frozen"],
                    "sample_id": "my_sample_id2",
                    "SM": "my_sample_id2",
                    "run_mode": "HiSeq High Output",
                },
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP7",
                    "tumor_type": "Normal",
                    "run_id": ["SEQRUN_0004"],
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
                "patient_id": "C-PPPPP7",
                "run_id": ["SEQRUN_0004"],
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
        missing normal for sample 99990_D_1; querying patient C-PPPPP7
        """
        # Load fixtures:
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "99990_D.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "99990_D.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP7",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "tumor_type": "Tumor",
                "SM": "99990_D_1",
                "sample_id": "99990_D_1",
                "run_mode": "hiseq",
            }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "normal": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_C_PPPPP7_N001_d_FCELLAAAA4"],
                    "LB": "99990_D_2",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA4"],
                    "R1": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D/Sample_31-N_IGO_99990_D_2/31-N_IGO_99990_D_2_S14_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("aef306b4-7d85-4c9f-b9a4-a115154f73bf")],
                    "R2": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D/Sample_31-N_IGO_99990_D_2/31-N_IGO_99990_D_2_S14_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("9e47ba2f-093a-4233-8339-fed03e159b3f")],
                    "bam": [],
                    "bam_bid": [],
                    "SM": "s_C_PPPPP7_N001_d",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_2",
                    "patient_id": "C-PPPPP7",
                    "request_id": "99990_D",
                    "run_id": ["SEQRUN_0004"],
                    "run_mode": "hiseq",
                    "preservation_type": ["Frozen"],
                    "run_date": ["2019-12-12"],
                    "species": "Human",
                    "specimen_type": "Blood",
                    "tumor_type": "Normal",
                    "pi": "Test Investigator",
                    "pi_email": "email@internet.com",
                }
            ],
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_1",
                    "SM": "99990_D_1",
                    "patient_id": "C-PPPPP7",
                    "run_id": ["SEQRUN_0004"],
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
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D.filemetadata.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99992_C.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99992_C.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 14)
        self.assertTrue(len(FileMetadata.objects.all()) == 18)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP7",
                "tumor_type": "Tumor",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["Frozen"],
                "SM": "99990_D_1",
                "sample_id": "99990_D_1",
                "run_mode": "hiseq",
            }
        ]
        pairs = compile_pairs(samples)
        expected_pairs = {
            "normal": [
                {
                    "CN": "MSKCC",
                    "ID": ["s_C_PPPPP7_N001_d_FCELLAAAA4"],
                    "LB": "99990_D_2",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA4"],
                    "R1": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D/Sample_31-N_IGO_99990_D_2/31-N_IGO_99990_D_2_S14_R1_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("aef306b47d854c9fb9a4a115154f73bf")],
                    "R2": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D/Sample_31-N_IGO_99990_D_2/31-N_IGO_99990_D_2_S14_R2_001.fastq.gz"
                    ],
                    "R2_bid": [UUID("9e47ba2f093a42338339fed03e159b3f")],
                    "bam": [],
                    "bam_bid": [],
                    "SM": "s_C_PPPPP7_N001_d",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_2",
                    "patient_id": "C-PPPPP7",
                    "request_id": "99990_D",
                    "run_id": ["SEQRUN_0004"],
                    "run_mode": "hiseq",
                    "preservation_type": ["Frozen"],
                    "run_date": ["2019-12-12"],
                    "species": "Human",
                    "specimen_type": "Blood",
                    "tumor_type": "Normal",
                    "pi": "Test Investigator",
                    "pi_email": "email@internet.com",
                }
            ],
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_1",
                    "SM": "99990_D_1",
                    "patient_id": "C-PPPPP7",
                    "run_id": ["SEQRUN_0004"],
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
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_2.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_2.filemetadata.json"), verbosity=0)
        # only tumors
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_3.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_3.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 4)
        self.assertTrue(len(FileMetadata.objects.all()) == 4)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP3",
                "tumor_type": "Tumor",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["EDTA-Streck"],
                "sample_id": "99990_D_3_5",
                "SM": "99990_D_3_5",
                "request_id": "99990_D_3",
                "run_mode": "hiseq",
            }
        ]

        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["EDTA-Streck"],
                    "tumor_type": "Tumor",
                    "sample_id": "99990_D_3_5",
                    "SM": "99990_D_3_5",
                    "request_id": "99990_D_3",
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA4"],
                    "LB": "99990_D_2_3",
                    "tumor_type": "Normal",
                    "ID": ["s_C_PPPPP3_N001_d_FCELLAAAA4"],
                    "SM": "s_C_PPPPP3_N001_d",
                    "species": "Human",
                    "patient_id": "C-PPPPP3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_2_3",
                    "run_date": ["2019-12-12"],
                    "specimen_type": "Blood",
                    "R1": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D_2/Sample_SAMPLE_N_001_IGO_99990_D_2_3/SAMPLE_N_001_IGO_99990_D_2_3_S15_R1_001.fastq.gz"
                    ],
                    "R2": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D_2/Sample_SAMPLE_N_001_IGO_99990_D_2_3/SAMPLE_N_001_IGO_99990_D_2_3_S15_R2_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("7a3bceb31af84d3da1583731c83aeb5a")],
                    "R2_bid": [UUID("ecf003cdbd304e909d180d99e7fd79d3")],
                    "bam": [],
                    "bam_bid": [],
                    "request_id": "99990_D_2",
                    "run_id": ["SEQRUN_0004"],
                    "run_mode": "hiseq",
                    "preservation_type": ["EDTA-Streck"],
                    "pi": "Test Investigator",
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
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_2.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_2.filemetadata.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_4.file.json"), verbosity=0)
        call_command("loaddata", os.path.join(settings.TEST_FIXTURE_DIR, "99990_D_4.filemetadata.json"), verbosity=0)

        # check the total number of db entries now
        self.assertTrue(len(File.objects.all()) == 4)
        self.assertTrue(len(FileMetadata.objects.all()) == 4)

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP3",
                "tumor_type": "Tumor",
                "sample_id": "99990_D_3_5",
                "SM": "99990_D_3_5",
                "request_id": "99990_D_3",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["EDTA-Streck"],
                "run_mode": "hiseq",
            }
        ]

        pairs = compile_pairs(samples)
        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Tumor",
                    "sample_id": "99990_D_3_5",
                    "SM": "99990_D_3_5",
                    "request_id": "99990_D_3",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["EDTA-Streck"],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA4"],
                    "LB": "99990_D_4_3",
                    "tumor_type": "Normal",
                    "ID": ["s_C_PPPPP3_N001_d_FCELLAAAA4"],
                    "SM": "s_C_PPPPP3_N001_d",
                    "species": "Human",
                    "patient_id": "C-PPPPP3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_4_3",
                    "run_date": ["2019-12-13"],
                    "specimen_type": "Blood",
                    "R1": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D_4/Sample_SAMPLE_N_001_IGO_99990_D_4_3/SAMPLE_N_001_IGO_99990_D_4_3_S15_R1_001.fastq.gz"
                    ],
                    "R2": [
                        "/data/archive/fastq/SEQRUN_0004_BFCELLAAAA4/Project_99990_D_4/Sample_SAMPLE_N_001_IGO_99990_D_4_3/SAMPLE_N_001_IGO_99990_D_4_3_S15_R2_001.fastq.gz"
                    ],
                    "R1_bid": [UUID("404ad544428c405f967aa6920d091148")],
                    "R2_bid": [UUID("19703ff82e144f608d57891df80b2858")],
                    "bam": [],
                    "bam_bid": [],
                    "request_id": "99990_D_4",
                    "run_id": ["SEQRUN_0004"],
                    "preservation_type": ["EDTA-Streck"],
                    "pi": "Test Investigator",
                    "pi_email": "email@internet.com",
                    "run_mode": "hiseq",
                }
            ],
        }

        self.assertTrue(pairs == expected_pairs)

    def test_compile_pairs_pooled_normal_and_dmp_bam(self):
        """
        Test that a DMP bam can be found for a tumor sample without any normal in the current request or other requests

        Start with no Normals and add them in reverse order of the Pairing priority (as per docstring header in this document)
        and make sure each added Normal results in the correct pairing
        """
        lims_filegroup_instance = FileGroup.objects.get(name="LIMS")
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
        dmp_bam_filegroup_instance = FileGroup.objects.get(name="DMP BAMs")
        bam_filetype_instance = FileType.objects.get(name="bam")

        settings.POOLED_NORMAL_FILE_GROUP = str(poolednormal_filegroup_instance.id)

        # generate tumor samples
        # Sample 1 C-PPPPP3
        tumor1_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-PPPPP3.R1.fastq",
            path="/C-PPPPP3.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=tumor1_R1_file_instance,
            metadata={
                "R": "R1",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "99990_D_3_5",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-PPPPP3",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-PPPPP3-R001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Tumor",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Local Recurrence",
                "externalSampleId": "SAMPLE_T_001",
                "investigatorSampleId": "SAMPLE_T_001",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "HiSeq High Output",
            },
        )
        tumor1_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-PPPPP3.R2.fastq",
            path="/C-PPPPP3.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=tumor1_R2_file_instance,
            metadata={
                "R": "R2",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "99990_D_3_5",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-PPPPP3",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-PPPPP3-R001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Tumor",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Local Recurrence",
                "externalSampleId": "SAMPLE_T_001",
                "investigatorSampleId": "SAMPLE_T_001",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "HiSeq High Output",
            },
        )

        # Sample 2 C-ABCDEF ; dummy sample
        tumor2_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-ABCDEF.R1.fastq",
            path="/C-ABCDEF.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=tumor2_R1_file_instance,
            metadata={
                "R": "R1",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "Sample12345",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-ABCDEF",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-ABCDEF-R001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Tumor",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Local Recurrence",
                "externalSampleId": "SK_MEL_1234_T",
                "investigatorSampleId": "SK_MEL_1234_T",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "HiSeq High Output",
            },
        )
        tumor2_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-ABCDEF.R2.fastq",
            path="/C-ABCDEF.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=tumor2_R2_file_instance,
            metadata={
                "R": "R2",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "Sample12345",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-ABCDEF",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-ABCDEF-R001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Tumor",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Local Recurrence",
                "externalSampleId": "SK_MEL_1234_T",
                "investigatorSampleId": "SK_MEL_1234_T",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "HiSeq High Output",
            },
        )

        samples = [
            {
                "bait_set": "IMPACT468_BAITS",
                "patient_id": "C-PPPPP3",
                "tumor_type": "Tumor",
                "sample_id": "99990_D_3_5",
                "SM": "99990_D_3_5",
                "request_id": "99990_D_3",
                "run_id": ["SEQRUN_0008"],
                "preservation_type": ["Frozen"],
                "run_mode": "hiseq",
            }
        ]

        # add Pooled Normal from another run
        poolednormal_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R1.fastq",
            path="/FROZENPOOLEDNORMAL.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance,
            metadata={
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "bait_set": "IMPACT468_BAITS",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "preservation": "Frozen",
            },
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R2.fastq",
            path="/FROZENPOOLEDNORMAL.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R2_file_instance,
            metadata={
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "bait_set": "IMPACT468_BAITS",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "preservation": "Frozen",
            },
        )

        pairs = compile_pairs(samples)
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pairs["normal"][0]["R1_bid"].pop()
        pairs["normal"][0]["R2_bid"].pop()

        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Tumor",
                    "sample_id": "99990_D_3_5",
                    "SM": "99990_D_3_5",
                    "request_id": "99990_D_3",
                    "run_id": ["SEQRUN_0008"],
                    "preservation_type": ["Frozen"],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["PN_FCID_FROZENPOOLEDNORMAL"],
                    "LB": "FROZENPOOLEDNORMAL_SEQRUN_0008_1",
                    "tumor_type": "Normal",
                    "ID": ["FROZENPOOLEDNORMAL_SEQRUN_0008_PN_FCID_FROZENPOOLEDNORMAL"],
                    "SM": "FROZENPOOLEDNORMAL_SEQRUN_0008",
                    "species": "",
                    "patient_id": "PN_PATIENT_ID",
                    "bait_set": "IMPACT468",
                    "sample_id": "FROZENPOOLEDNORMAL_SEQRUN_0008",
                    "run_date": [""],
                    "specimen_type": "",
                    "R1": ["/FROZENPOOLEDNORMAL.R1.fastq"],
                    "R2": ["/FROZENPOOLEDNORMAL.R2.fastq"],
                    "R1_bid": [],  # UUID('cf065d86-3096-47b3-9b6f-cf711a1d6e0f')
                    "R2_bid": [],  # UUID('51232bdd-6b31-4a4d-80c4-3aef13965fcd')
                    "bam": [],
                    "bam_bid": [],
                    "specimen_type": "Pooled Normal",
                    "request_id": "FROZENPOOLEDNORMAL_SEQRUN_0008",
                    "pi": "",
                    "pi_email": "",
                    "run_id": ["SEQRUN_0008"],
                    "preservation_type": [["Frozen"]],
                    "run_mode": "",
                }
            ],
        }
        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (pn part): pairs ---\n",
            json.dumps(pairs, cls=UUIDEncoder),
        )
        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (pn part): expected ---\n",
            json.dumps(expected_pairs, cls=UUIDEncoder),
        )
        self.assertDictEqual(pairs, expected_pairs)

        # Add a DMP Bam for the tumor sample to the database
        dmp_bam_file_instance = File.objects.create(
            file_type=bam_filetype_instance,
            file_group=dmp_bam_filegroup_instance,
            file_name="C-PPPPP3.bam",
            path="/C-PPPPP3.bam",
        )
        FileMetadata.objects.create_or_update(
            file=dmp_bam_file_instance,
            version=1,
            metadata={
                "bai": "/C-PPPPP3.bai",
                "bam": "/C-PPPPP3.bam",
                "type": "N",
                "assay": "IM6",
                "sample": "P-1234567-N01-IM6",
                "anon_id": "ABCDEF-N",
                "patient": {
                    "cmo": "PPPPP3",
                    "dmp": "P-1234567",
                    "updated": "2020-03-19T23:57:51.941963Z",
                    "imported": "2020-03-19T23:57:51.941945Z",
                },
                "updated": "2020-03-25T19:45:16.421154Z",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "version": 1,
                "coverage": 648,
                "imported": "2020-03-25T19:45:16.421137Z",
                "cmo_assay": "IMPACT468",
                "tumor_type": "MBC",
                "external_id": "C-PPPPP3-N901-dZ-IM6",
                "sample_type": "0",
                "tissue_type": "Breast",
                "primary_site": "Breast",
                "project_name": "UK12344567890VB",
                "patient_group": "Group_12344567890",
                "part_c_consent": 1,
                "metastasis_site": "Not Applicable",
                "somatic_calling_status": "Matched",
                "major_allele_contamination": 0.452,
                "minor_allele_contamination": 0.00069,
            },
        )

        # test that the DMP bam gets chosen as the sample's matched normal now instead of the pooled normal
        pairs = compile_pairs(samples)

        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Tumor",
                    "sample_id": "99990_D_3_5",
                    "SM": "99990_D_3_5",
                    "request_id": "99990_D_3",
                    "run_id": ["SEQRUN_0008"],
                    "preservation_type": ["Frozen"],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["DMP_FCID_DMP_BARCODEIDX"],
                    "LB": "C-PPPPP3-N901-dZ-IM6_1",
                    "tumor_type": "Normal",
                    "ID": ["s_C_PPPPP3_N901_dZ_IM6_DMP_FCID_DMP_BARCODEIDX"],
                    "SM": "s_C_PPPPP3_N901_dZ_IM6",
                    "species": "",
                    "patient_id": "C-PPPPP3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "s_C_PPPPP3_N901_dZ_IM6",
                    "run_date": [""],
                    "specimen_type": "DMP",
                    "R1": [[]],
                    "R2": [[]],
                    "R1_bid": [[]],
                    "R2_bid": [[]],
                    "bam": ["/C-PPPPP3.bam"],
                    "bam_bid": [],  # UUID('77b9a78f-1bed-475c-9799-c18a6f57b347')
                    "request_id": None,
                    "pi": "",
                    "pi_email": "",
                    "run_id": [""],
                    "preservation_type": [""],
                    "run_mode": "",
                }
            ],
        }

        # remove the bam_bid for testing because it is non-deterministic
        # TODO: mock this ^^
        pairs["normal"][0]["bam_bid"].pop()

        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (dmp part): pairs ---\n",
            json.dumps(pairs, cls=UUIDEncoder),
        )
        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (dmp part): expected ---\n",
            json.dumps(expected_pairs, cls=UUIDEncoder),
        )
        self.assertDictEqual(pairs, expected_pairs)

        # Now add a matched normal to the original request for the sample
        # Sample 1 C-PPPPP3
        normal1_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-PPPPP3-N.R1.fastq",
            path="/C-PPPPP3-N.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=normal1_R1_file_instance,
            metadata={
                "R": "R1",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "99990_D_2_3",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-PPPPP3",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-PPPPP3-N001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Normal",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                "externalSampleId": "SK_MEL_1091A_N",
                "investigatorSampleId": "SK_MEL_1091A_N",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "HiSeq",
            },
        )
        normal1_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=lims_filegroup_instance,
            file_name="C-PPPPP3-N.R2.fastq",
            path="/C-PPPPP3-N.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=normal1_R2_file_instance,
            metadata={
                "R": "R2",
                "sex": "F",
                "runId": "SEQRUN_0008",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "baitSet": "IMPACT468_BAITS",
                "species": "Human",
                settings.SAMPLE_ID_METADATA_KEY: "99990_D_2_3",
                settings.LIBRARY_ID_METADATA_KEY: None,
                "flowCellId": "FCELLAAAA6",
                "barcodeId": "DUAL_IDT_LIB_267",
                "barcodeIndex": "GTATTGGC-PPPP14",
                "runDate": "2019-12-17",
                settings.PATIENT_ID_METADATA_KEY: "C-PPPPP3",
                settings.REQUEST_ID_METADATA_KEY: "99990_D_3",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-PPPPP3-N001-d",
                settings.IGO_COMPLETE_METADATA_KEY: True,
                settings.ONCOTREE_METADATA_KEY: "MEL",
                "preservation": "Frozen",
                "sampleOrigin": "Tissue",
                settings.SAMPLE_CLASS_METADATA_KEY: "Resection",
                "tumorOrNormal": "Normal",
                settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                "externalSampleId": "SK_MEL_1091A_N",
                "investigatorSampleId": "SK_MEL_1091A_N",
                "labHeadEmail": "",
                "labHeadName": "",
                "runMode": "Hiseq",
            },
        )

        # test that the paired normal from the same request gets chosen instead for the pairing
        pairs = compile_pairs(samples)
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pairs["normal"][0]["R1_bid"].pop()
        pairs["normal"][0]["R2_bid"].pop()

        expected_pairs = {
            "tumor": [
                {
                    "bait_set": "IMPACT468_BAITS",
                    "patient_id": "C-PPPPP3",
                    "tumor_type": "Tumor",
                    "sample_id": "99990_D_3_5",
                    "SM": "99990_D_3_5",
                    "request_id": "99990_D_3",
                    "run_id": ["SEQRUN_0008"],
                    "preservation_type": ["Frozen"],
                    "run_mode": "hiseq",
                }
            ],
            "normal": [
                {
                    "CN": "MSKCC",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA6_GTATTGGC-PPPP14"],
                    "LB": "s_C_PPPPP3_N001_d_1",
                    "tumor_type": "Normal",
                    "ID": ["s_C_PPPPP3_N001_d_FCELLAAAA6_GTATTGGC-PPPP14"],
                    "SM": "s_C_PPPPP3_N001_d",
                    "species": "Human",
                    "patient_id": "C-PPPPP3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "99990_D_2_3",
                    "run_date": ["2019-12-17"],
                    "specimen_type": "Resection",
                    "R1": ["/C-PPPPP3-N.R1.fastq"],
                    "R2": ["/C-PPPPP3-N.R2.fastq"],
                    "R1_bid": [],  # UUID('bfb94fe6-bf46-431a-8f72-6ee47ee72fc9')
                    "R2_bid": [],  # UUID('1e8b68f8-c333-499c-b22d-50fbef2d2ea7')
                    "bam": [],
                    "bam_bid": [],
                    "request_id": "99990_D_3",
                    "pi": "",
                    "pi_email": "",
                    "run_id": ["SEQRUN_0008"],
                    "preservation_type": ["Frozen"],
                    "run_mode": "hiseq",
                }
            ],
        }

        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (third variation): pairs ---\n",
            json.dumps(pairs, cls=UUIDEncoder),
        )
        print(
            "Running test_compile_pairs_pooled_normal_and_dmp_bam (third variation): expected ---\n",
            json.dumps(expected_pairs, cls=UUIDEncoder),
        )
        self.assertDictEqual(pairs, expected_pairs)

    def test_compile_pairs_custom1(self):
        """
        Test the ability to compile pairs with a custom sample set

        TODO: what pair attributes is this testing?
        """
        samples = [
            {
                "CN": "MSKCC",
                "ID": ["s_juno_argos_demo1_3_FCELLAAAA4"],
                "LB": "juno_argos_demo1_3",
                "PL": "Illumina",
                "PU": ["FCELLAAAA4"],
                "R1": ["/data/pipeline/test/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                "R1_bid": [UUID("a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac")],
                "R2": ["/data/pipeline/test/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                "R2_bid": [UUID("c71c259a-ebc0-4490-9af1-bc99387a70d7")],
                "bam": [],
                "bam_bid": [],
                "SM": "s_juno_argos_demo1_3",
                "bait_set": "IMPACT468_BAITS",
                "sample_id": "s_juno_argos_demo1_3",
                "patient_id": "DU874145",
                "request_id": "juno_argos_demo1",
                "run_id": ["SEQRUN_0004"],
                "preservation_type": ["EDTA-Streck"],
                "run_date": ["2019-12-12"],
                "species": "Human",
                "specimen_type": "Blood",
                "tumor_type": "Normal",
                "run_mode": "hiseq",
            },
            {
                "CN": "MSKCC",
                "ID": ["s_juno_argos_demo1_5_FCELLAAAA6_GTATTGGC-PPPP14"],
                "LB": "juno_argos_demo1_5_1_1_1",
                "PL": "Illumina",
                "PU": ["FCELLAAAA6_GTATTGGC-PPPP14"],
                "R1": ["/data/pipeline/test/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                "R1_bid": [UUID("d2d8ed36-d8f4-4e93-b038-d38328fad021")],
                "R2": ["/data/pipeline/test/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                "R2_bid": [UUID("2f77f3ac-ab25-4a02-90bd-86542401ac89")],
                "bam": [],
                "bam_bid": [],
                "SM": "s_juno_argos_demo1_5",
                "bait_set": "IMPACT468_BAITS",
                "sample_id": "s_juno_argos_demo1_5",
                "patient_id": "DU874145",
                "request_id": "juno_argos_demo1",
                "run_id": ["SEQRUN_0004"],
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
                    "ID": ["s_juno_argos_demo1_5_FCELLAAAA6_GTATTGGC-PPPP14"],
                    "LB": "juno_argos_demo1_5_1_1_1",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA6_GTATTGGC-PPPP14"],
                    "R1": ["/data/pipeline/test/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                    "R1_bid": [UUID("d2d8ed36-d8f4-4e93-b038-d38328fad021")],
                    "R2": ["/data/pipeline/test/fastq/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                    "R2_bid": [UUID("2f77f3ac-ab25-4a02-90bd-86542401ac89")],
                    "SM": "s_juno_argos_demo1_5",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "s_juno_argos_demo1_5",
                    "patient_id": "DU874145",
                    "request_id": "juno_argos_demo1",
                    "run_id": ["SEQRUN_0004"],
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
                    "ID": ["s_juno_argos_demo1_3_FCELLAAAA4"],
                    "LB": "juno_argos_demo1_3",
                    "PL": "Illumina",
                    "PU": ["FCELLAAAA4"],
                    "R1": ["/data/pipeline/test/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"],
                    "R1_bid": [UUID("a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac")],
                    "R2": ["/data/pipeline/test/fastq/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"],
                    "R2_bid": [UUID("c71c259a-ebc0-4490-9af1-bc99387a70d7")],
                    "SM": "s_juno_argos_demo1_3",
                    "bait_set": "IMPACT468_BAITS",
                    "sample_id": "s_juno_argos_demo1_3",
                    "patient_id": "DU874145",
                    "request_id": "juno_argos_demo1",
                    "run_id": ["SEQRUN_0004"],
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
