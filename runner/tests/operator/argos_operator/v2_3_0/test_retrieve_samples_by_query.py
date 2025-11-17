import os
from uuid import UUID
import json
from datetime import datetime
from django.test import TestCase, override_settings
from django.db.models import Prefetch, Q
from runner.operator.argos_operator.v2_3_0.bin.retrieve_samples_by_query import build_dmp_query
from runner.operator.argos_operator.v2_3_0.bin.retrieve_samples_by_query import get_pooled_normals
from runner.operator.argos_operator.v2_3_0.bin.retrieve_samples_by_query import build_run_id_query
from runner.operator.argos_operator.v2_3_0.bin.retrieve_samples_by_query import build_preservation_query
from runner.operator.argos_operator.v2_3_0.bin.retrieve_samples_by_query import get_descriptor
from runner.tests.operator.argos_operator.v2_3_0.test_pair_request import UUIDEncoder
from django.conf import settings
from django.core.management import call_command
from file_system.models import File, FileMetadata, FileGroup, FileType, PooledNormal


class TestRetrieveSamplesByQuery(TestCase):
    # load fixtures for the test case temp db
    fixtures = ["file_system.filegroup.json", "file_system.filetype.json", "file_system.storage.json"]

    def setUp(self):
        # Override POOLED_NORMAL_FILE_GROUP setting
        super().setUp()

        try:
            call_command("loaddata", "file_system.filegroup.json")
            settings.POOLED_NORMAL_FILE_GROUP = str(FileGroup.objects.get(name="Pooled Normal").id)
        except Exception as e:
            print(f"Error in setUp: {e}")

    def test_build_run_id_query(self):
        """
        Test that a run id query is built correctly
        """
        run_ids = ["bar"]
        query = build_run_id_query(run_ids)
        # (AND: (('filemetadata__metadata__runId', 'bar'))
        expected_query = Q(metadata__runId="bar")
        self.assertEqual(query, expected_query)

        # run them through set then back to list to ensure ordering for testing
        run_ids = set(["bar", "baz"])
        query = build_run_id_query(run_ids)
        # query.__dict__
        # {'children': [('filemetadata__metadata__runId', 'baz'), ('filemetadata__metadata__runId', 'bar')], 'connector': 'OR', 'negated': False}

        # order not guaranteed due to usage of set inside build_run_id_query
        expected_query = Q(filemetadata__metadata__runId="bar") | Q(filemetadata__metadata__runId="baz")
        # (OR: ('filemetadata__metadata__runId', 'baz'), ('filemetadata__metadata__runId', 'bar'))

        self.assertTrue(("metadata__runId", "baz") in query.__dict__["children"])
        self.assertTrue(("metadata__runId", "bar") in query.__dict__["children"])
        self.assertTrue(query.__dict__["connector"] == "OR")
        self.assertTrue(query.__dict__["negated"] == False)

    def test_build_preservation_query(self):
        """
        Test that a preservation type query is built correctly
        Test different combinations of valid and invalid preservation types, with and without caps
        """
        preservation_types = list(set(["foo", "bar"]))
        query = build_preservation_query(preservation_types)
        # TODO: why does this give the preservation type of "FROZEN"?
        expected_query = Q(metadata__preservation__iexact="FROZEN")
        # expected_query = {'metadata__preservation__iexact': "FROZEN"}
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["foo", "frozen"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FROZEN")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["foo", "ffpe"]))
        query = build_preservation_query(preservation_types)
        # TODO: why does this give the preservation type of "FFPE"?
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["foo", "FFPE"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["frozen", "ffpe"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["frozen", "FFPE"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["FROZEN", "ffpe"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["FROZEN", "FFPE"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["FFPE"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["ffpe"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FFPE")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["frozen"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FROZEN")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["Frozen"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FROZEN")
        self.assertEqual(query, expected_query)

        preservation_types = list(set(["FROZEN"]))
        query = build_preservation_query(preservation_types)
        expected_query = Q(metadata__preservation__iexact="FROZEN")
        self.assertEqual(query, expected_query)

    def test_get_descriptor1(self):
        """
        Test that re-labeled descriptor is returned when needed
        """
        # create some Pooled Normals
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
        poolednormal_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R1.fastq",
            path="/FROZENPOOLEDNORMAL.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance,
            metadata={
                settings.RECIPE_METADATA_KEY: "IMPACT468",
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
                settings.RECIPE_METADATA_KEY: "IMPACT468",
            },
        )
        pooled_normals = FileMetadata.objects.all()

        pooled_normals, descriptor, sample_name = get_descriptor(
            bait_set="IMPACT468_BAITS", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=pooled_normals
        )
        self.assertEqual(descriptor, "IMPACT468")

        pooeld_normals, descriptor, sample_name = get_descriptor(
            bait_set="IMPACT468", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=pooled_normals
        )
        self.assertEqual(descriptor, "IMPACT468")

    def test_get_descriptor2(self):
        """
        Test that no descriptor is returned when its not needed
        """
        # create some Pooled Normals
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
        poolednormal_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R1.fastq",
            path="/FROZENPOOLEDNORMAL.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance,
            metadata={
                settings.RECIPE_METADATA_KEY: "foo_IMPACT468_bar",
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
                settings.RECIPE_METADATA_KEY: "foo_IMPACT468_bar",
            },
        )
        all_pooled_normals = FileMetadata.objects.all()

        pooled_normals, descriptor, sample_name = get_descriptor(
            bait_set="IMPACT468", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=all_pooled_normals
        )
        self.assertEqual(descriptor, None)

        pooled_normals, descriptor, sample_name = get_descriptor(
            bait_set="IMPACT468_bar", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=all_pooled_normals
        )
        self.assertEqual(descriptor, None)

        pooled_normals, descriptor, sample_name = get_descriptor(
            bait_set="foo_IMPACT468", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=all_pooled_normals
        )
        self.assertEqual(descriptor, None)

        pooled_normals, descriptor, sample_name = get_descriptor(
            bait_set="foo_IMPACT468_bar", preservation_types=["FROZEN"], run_ids=[""], pooled_normals=all_pooled_normals
        )
        self.assertEqual(descriptor, "foo_IMPACT468_bar")

    def test_get_pooled_normals1(self):
        """
        Test that Pooled Normals can be retrieved correctly

        This is the legacy pooled normal test - i.e., pulls from Pooled Normal FileGroup
        metadata instead of from the PooledNormal model (introduced when NovaSeq X was added)
        """
        # test that an empty database and irrelevant args returns None
        pooled_normals = get_pooled_normals(run_ids=["foo"], preservation_types=["bar"], bait_set="baz")
        self.assertEqual(pooled_normals, None)

        # start adding Pooled Normals to the database
        ### Because of updates to how FileRepository works, this doesn't actually work anymore
        ## FileGroup for pooled normal needs to be set to settings.POOLED_NORMAL_FILE_GROUP
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
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
                "runId": "PITT_0439",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "baitSet": "IMPACT468_BAITS",
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
                "runId": "PITT_0439",
                settings.RECIPE_METADATA_KEY: "IMPACT468",
                "sequencingCenter": "MSKCC",
                "platform": "Illumina",
                "baitSet": "IMPACT468_BAITS",
                "preservation": "Frozen",
            },
        )

        pooled_normals = get_pooled_normals(
            run_ids=["PITT_0439"], preservation_types=["Frozen"], bait_set="IMPACT468_BAITS"
        )
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pooled_normals["R1_bid"].pop()
        pooled_normals["R2_bid"].pop()

        expected_pooled_normals = {
            "CN": "MSKCC",
            "PL": "Illumina",
            "PU": ["PN_FCID_FROZENPOOLEDNORMAL"],
            "LB": "FROZENPOOLEDNORMAL_PITT_0439_1",
            "tumor_type": "Normal",
            "ID": ["FROZENPOOLEDNORMAL_PITT_0439_PN_FCID_FROZENPOOLEDNORMAL"],
            "SM": "FROZENPOOLEDNORMAL_PITT_0439",
            "species": "",
            "patient_id": "PN_PATIENT_ID",
            "bait_set": "IMPACT468",
            "sample_id": "FROZENPOOLEDNORMAL_PITT_0439",
            "run_date": [""],
            "specimen_type": "Pooled Normal",
            "R1": ["/FROZENPOOLEDNORMAL.R1.fastq"],
            "R2": ["/FROZENPOOLEDNORMAL.R2.fastq"],
            "R1_bid": [],  # UUID('7268ac6e-e9a6-48e0-94f1-1c894280479b')
            "R2_bid": [],  # UUID('ec9817d1-d6f5-4f1d-9c0a-c82fc22d4daa')
            "bam": [],
            "bam_bid": [],
            "request_id": "FROZENPOOLEDNORMAL_PITT_0439",
            "pi": "",
            "pi_email": "",
            "run_id": ["PITT_0439"],
            "preservation_type": [["Frozen"]],
            "run_mode": "",
        }

        self.assertEqual(pooled_normals, expected_pooled_normals)

    def test_get_pooled_normals_novaseq_x(self):
        """
        Test that NovaSeq X FAUCI2 Pooled Normals can be retrieved correctly
        """
        # test that an empty database and irrelevant args returns None
        pooled_normals = get_pooled_normals(run_ids=["foo"], preservation_types=["bar"], bait_set="baz")
        self.assertEqual(pooled_normals, None)

        # Add pooled normals from the PooledNormal table
        PooledNormal.objects.update_or_create(
            machine="fauci2",
            bait_set="impact505_baits",
            gene_panel="hc_impact",
            preservation_type="frozen",
            run_date=datetime.strptime("01-01-2021", "%d-%m-%Y"),
            pooled_normals_paths=["/FROZENPOOLEDNORMAL.R1.fastq", "/FROZENPOOLEDNORMAL.R2.fastq"],
        )

        # start adding Pooled Normals to the database
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
        # add Pooled Normal from another run
        poolednormal_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R1.fastq",
            path="/FROZENPOOLEDNORMAL.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance,
            metadata={},
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R2.fastq",
            path="/FROZENPOOLEDNORMAL.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R2_file_instance,
            metadata={},
        )

        pooled_normals = get_pooled_normals(
            run_ids=["FAUCI2_0049"], preservation_types=["Frozen"], bait_set="IMPACT505_BAITS"
        )
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pooled_normals["R1_bid"].pop()
        pooled_normals["R2_bid"].pop()

        expected_pooled_normals = {
            "CN": "MSKCC",
            "PL": "Illumina",
            "PU": ["PN_FCID_FROZENPOOLEDNORMAL"],
            "LB": "IMPACT505_BAITS_FROZEN_FAUCI2_POOLEDNORMAL_1",
            "tumor_type": "Normal",
            "ID": ["IMPACT505_BAITS_FROZEN_FAUCI2_POOLEDNORMAL_PN_FCID_FROZENPOOLEDNORMAL"],
            "SM": "IMPACT505_BAITS_FROZEN_FAUCI2_POOLEDNORMAL",
            "species": "",
            "patient_id": "PN_PATIENT_ID",
            "bait_set": "impact505_baits",
            "sample_id": "IMPACT505_BAITS_FROZEN_FAUCI2_POOLEDNORMAL",
            "run_date": [""],
            "specimen_type": "Pooled Normal",
            "R1": ["/FROZENPOOLEDNORMAL.R1.fastq"],
            "R2": ["/FROZENPOOLEDNORMAL.R2.fastq"],
            "R1_bid": [],
            "R2_bid": [],
            "bam": [],
            "bam_bid": [],
            "request_id": "IMPACT505_BAITS_FROZEN_FAUCI2_POOLEDNORMAL",
            "pi": "",
            "pi_email": "",
            "run_id": ["FAUCI2_0049"],
            "preservation_type": [["Frozen"]],
            "run_mode": "",
        }

        self.assertEqual(pooled_normals, expected_pooled_normals)

    def test_get_pooled_normals_novaseq_x_multiple_records(self):
        """
        Test that NovaSeq X FAUCI2 Pooled Normals can be retrieved correctly

        This one pulls the record with the earliest run date
        """
        # test that an empty database and irrelevant args returns None
        pooled_normals = get_pooled_normals(run_ids=["foo"], preservation_types=["bar"], bait_set="baz")
        self.assertEqual(pooled_normals, None)

        # Add pooled normals from the PooledNormal table
        PooledNormal.objects.update_or_create(
            machine="fauci2",
            bait_set="impact505_baits",
            gene_panel="hc_impact",
            preservation_type="frozen",
            run_date=datetime.strptime("01-01-2021", "%d-%m-%Y"),
            pooled_normals_paths=["/FROZENPOOLEDNORMAL.R1.fastq", "/FROZENPOOLEDNORMAL.R2.fastq"],
        )

        PooledNormal.objects.update_or_create(
            machine="bono",
            bait_set="impact505_baits",
            gene_panel="hc_impact",
            preservation_type="frozen",
            run_date=datetime.strptime("01-01-1999", "%d-%m-%Y"),
            pooled_normals_paths=["/FROZENPOOLEDNORMAL.CORRECT.R1.fastq", "/FROZENPOOLEDNORMAL.CORRECT.R2.fastq"],
        )
        # start adding Pooled Normals to the database
        poolednormal_filegroup_instance = FileGroup.objects.get(name="Pooled Normal")
        fastq_filetype_instance = FileType.objects.get(name="fastq")
        # add Pooled Normal from another run
        poolednormal_R1_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R1.fastq",
            path="/FROZENPOOLEDNORMAL.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance,
            metadata={},
        )
        poolednormal_R2_file_instance = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.R2.fastq",
            path="/FROZENPOOLEDNORMAL.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R2_file_instance,
            metadata={},
        )

        poolednormal_R1_file_instance_earliest = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.CORRECT.R1.fastq",
            path="/FROZENPOOLEDNORMAL.CORRECT.R1.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R1_file_instance_earliest,
            metadata={},
        )
        poolednormal_R2_file_instance_earliest = File.objects.create(
            file_type=fastq_filetype_instance,
            file_group=poolednormal_filegroup_instance,
            file_name="FROZENPOOLEDNORMAL.CORRECT.R2.fastq",
            path="/FROZENPOOLEDNORMAL.CORRECT.R2.fastq",
        )
        FileMetadata.objects.create_or_update(
            file=poolednormal_R2_file_instance_earliest,
            metadata={},
        )

        pooled_normals = get_pooled_normals(
            run_ids=["FAUCI2_0049", "BONO_12314"], preservation_types=["Frozen"], bait_set="IMPACT505_BAITS"
        )
        # remove the R1_bid and R2_bid for testing because they are non-deterministic
        # TODO: mock this ^^
        pooled_normals["R1_bid"].pop()
        pooled_normals["R2_bid"].pop()

        expected_pooled_normals = {
            "CN": "MSKCC",
            "PL": "Illumina",
            "PU": ["PN_FCID_FROZENPOOLEDNORMAL"],
            "LB": "IMPACT505_BAITS_FROZEN_BONO_POOLEDNORMAL_1",
            "tumor_type": "Normal",
            "ID": ["IMPACT505_BAITS_FROZEN_BONO_POOLEDNORMAL_PN_FCID_FROZENPOOLEDNORMAL"],
            "SM": "IMPACT505_BAITS_FROZEN_BONO_POOLEDNORMAL",
            "species": "",
            "patient_id": "PN_PATIENT_ID",
            "bait_set": "impact505_baits",
            "sample_id": "IMPACT505_BAITS_FROZEN_BONO_POOLEDNORMAL",
            "run_date": [""],
            "specimen_type": "Pooled Normal",
            "R1": ["/FROZENPOOLEDNORMAL.CORRECT.R1.fastq"],
            "R2": ["/FROZENPOOLEDNORMAL.CORRECT.R2.fastq"],
            "R1_bid": [],
            "R2_bid": [],
            "bam": [],
            "bam_bid": [],
            "request_id": "IMPACT505_BAITS_FROZEN_BONO_POOLEDNORMAL",
            "pi": "",
            "pi_email": "",
            "run_id": ["FAUCI2_0049", "BONO_12314"],
            "preservation_type": [["Frozen"]],
            "run_mode": "",
        }

        pooled_normals_sorted = {k: sorted(v) for k, v in pooled_normals.items()}
        expected_pooled_normals_sorted = {k: sorted(v) for k, v in expected_pooled_normals.items()}

        self.assertEqual(pooled_normals_sorted, expected_pooled_normals_sorted)
