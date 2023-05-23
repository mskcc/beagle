"""
Test for constructing ultron inputs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.ultron.v1_0_0.phase1 import UltronOperator, SampleData, BamData
from beagle_etl.models import Operator
from notifier.models import JobGroup
from runner.models import Run, Port
from file_system.models import File, FileMetadata, FileGroup, FileType
from file_system.repository.file_repository import FileRepository
from django.conf import settings
from django.core.management import call_command


class TestUltron(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "runner.operator_trigger.json",
        "runner.operator_run.json",
        "runner.pipeline.json",
        "beagle_etl.operator.json",
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "DMP_data.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.run.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.samples.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.files.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.port.output.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.port.input.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.run.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.samples.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.files.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.port.output.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.port.input.json",
    ]

    def setUp(self):
        os.environ["TMPDIR"] = ""
        self.run_ids = ["28ca34e8-9d4c-4543-9fc7-981bf5f6a97f", "4d9c8213-df56-4a0f-8d86-ce2bd8349c59"]
        self.sample_ids = [
            ["9af6ab44-0117-479c-aeab-d7a774f4c9b9", "f750a0a2-5fe5-440c-a7d4-e042fe3c470c"],
            ["0ef3577f-e57e-4e99-82b2-efc96c41032e", "f750a0a2-5fe5-440c-a7d4-e042fe3c470c"],
        ]
        self.file_metadata_ids = [
            [
                "c28794bf-de45-40a1-b32f-5659263ddde3",
                "969b2757-c116-4569-b39f-0294335dfea8",
                "d769789b-7938-4ac5-b897-121d7623c61a",
                "6226e750-ba7a-4144-a9d4-835e93dc31ea",
            ],
            [
                "c53b78d4-3b13-4029-8dbc-bfa5f254c515",
                "d769789b-7938-4ac5-b897-121d7623c61a",
                "6226e750-ba7a-4144-a9d4-835e93dc31ea",
                "b8142135-a50f-4090-b5e4-0f92587c9a96",
            ],
        ]
        self.first_dmp_bam_metadata_id = "638dbd71-0d7d-46bb-833d-25b7d90651c7"
        self.first_dmp_mutations_extended_id = "92a88d6d-92cc-4107-a334-d11c75efd8d6"
        self.first_dmp_mutations_extended = "/path/to/P-0000000-T01-IM6.txt"
        self.first_dmp_dmp_sample_name = "P-0000001-T01-IM6"
        self.first_run_expected_inputs = {
            "unindexed_bam_files": [
                {"class": "File", "location": "juno:///path/to/P-00000001-T.bam"},
                {"class": "File", "location": "juno:///path/to/P-00000002-T.bam"},
            ],
            "unindexed_sample_ids": ["P-0000001-T01-IM6", "P-0000000-T01-IM6"],
            "unindexed_maf_files": [
                {"class": "File", "location": "juno:///path/to/P-0000001-T01-IM6.txt"},
                {"class": "File", "location": "juno:///path/to/P-0000002-T01-IM6.txt"},
            ],
            "maf_files": [
                {
                    "class": "File",
                    "location": "juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.s_C_ALLANT_N002_d.muts.maf",
                }
            ],
            "bam_files": [
                {
                    "class": "File",
                    "location": "juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.rg.md.abra.printreads.bam",
                    "secondaryFiles": [
                        {
                            "class": "File",
                            "location": "juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.rg.md.abra.printreads.bai",
                        }
                    ],
                }
            ],
            "sample_ids": ["s_C_ALLANT_T003_d"],
            "ref_fasta": {"class": "File", "location": "juno:///juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta"},
            "exac_filter": {
                "class": "File",
                "location": "juno:///juno/work/ci/resources/vep/cache/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz",
            },
        }
        self.maf_runner_ports = ["7f743915-a0d6-466c-b1eb-3f8501089a36", "b946625d-2753-4e5a-89b8-cc08beb1bc40"]
        self.expected_output_directory = "/juno/work/pi/beagle/output/argos_pair_sv/argos/ALN-REQ-ID/1.1.2/"
        self.expected_project_prefix = "ALN-REQ-ID"

    def test_construct_output_directory(self):
        """
        Test the creation of the output directory

        Since this tests per run_id, this also tests project prefix retrieval (part of output dir path)
        """
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=12)
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id
        )
        for run_id in self.run_ids:
            output_directory = ultron_operator._get_output_directory(run_id)
            expected_output_directory_with_timestamp = os.path.join(
                self.expected_output_directory, job_group.created_date.strftime("%Y%m%d_%H_%M_%f"), "analysis"
            )
            self.assertEqual(output_directory, expected_output_directory_with_timestamp)

    def test_construct_ultron_job(self):
        """
        Test the creation of an ultron job
        """
        sample = FileMetadata.objects.get(id=self.file_metadata_ids[0][0]).metadata[settings.SAMPLE_ID_METADATA_KEY]
        input_json = {
            "argos_version_string": "1.1.2",
            "exac_filter": {
                "class": "File",
                "location": "juno:///juno/work/ci/resources/vep/cache/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz",
            },
            "fillout_output_fname": "ALN-REQ-ID.fillout.maf",
            "is_impact": True,
            "ref_fasta": {"class": "File", "location": "juno:///juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta"},
            "sample_groups": [
                [
                    {
                        "bam_file": {
                            "class": "File",
                            "location": "juno:///juno/work/ci/voyager-output/4d9c8213-df56-4a0f-8d86-ce2bd8349c59/s_C_ALLANT_T001_d.rg.md.abra.printreads.bam",
                        },
                        "maf_file": {
                            "class": "File",
                            "location": "juno:///juno/work/ci/voyager-output/4d9c8213-df56-4a0f-8d86-ce2bd8349c59/s_C_ALLANT_T001_d.s_C_ALLANT_N002_d.muts.maf",
                        },
                        "normal_id": "s_C_ALLANT_N002_d",
                        "prefilter": True,
                        "sample_id": "s_C_ALLANT_T001_d",
                        "sample_type": "research",
                    },
                    {
                        "bam_file": {"class": "File", "location": "juno:///path/to/P-00000002-T.bam"},
                        "maf_file": {"class": "File", "location": "juno:///path/to/P-0000002-T01-IM6.txt"},
                        "normal_id": "DMP_NORMAL",
                        "prefilter": False,
                        "sample_id": "P-0000002-T01-IM6",
                        "sample_type": "clinical",
                    },
                    {
                        "bam_file": {"class": "File", "location": "juno:///path/to/00000001-T.bam"},
                        "maf_file": {"class": "File", "location": "juno:///path/to/P-0000000-T01-IM6.txt"},
                        "normal_id": "DMP_NORMAL",
                        "prefilter": False,
                        "sample_id": "P-0000001-T01-IM6",
                        "sample_type": "clinical",
                    },
                ],
                [
                    {
                        "bam_file": {
                            "class": "File",
                            "location": "juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.rg.md.abra.printreads.bam",
                        },
                        "maf_file": {
                            "class": "File",
                            "location": "juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.s_C_ALLANT_N002_d.muts.maf",
                        },
                        "normal_id": "s_C_ALLANT_N002_d",
                        "prefilter": True,
                        "sample_id": "s_C_ALLANT_T003_d",
                        "sample_type": "research",
                    },
                    {
                        "bam_file": {"class": "File", "location": "juno:///path/to/P-00000002-T.bam"},
                        "maf_file": {"class": "File", "location": "juno:///path/to/P-0000002-T01-IM6.txt"},
                        "normal_id": "DMP_NORMAL",
                        "prefilter": False,
                        "sample_id": "P-0000002-T01-IM6",
                        "sample_type": "clinical",
                    },
                    {
                        "bam_file": {"class": "File", "location": "juno:///path/to/00000001-T.bam"},
                        "maf_file": {"class": "File", "location": "juno:///path/to/P-0000000-T01-IM6.txt"},
                        "normal_id": "DMP_NORMAL",
                        "prefilter": False,
                        "sample_id": "P-0000001-T01-IM6",
                        "sample_type": "clinical",
                    },
                ],
            ],
        }
        operator_model = Operator.objects.get(id=12)
        job_group = JobGroup()
        job_group.save()
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id
        )
        sample_groups = ultron_operator._build_sample_groups(self.run_ids)
        inputs = dict(sample_groups=sample_groups)
        rep_run_id = self.run_ids[0]  # required; because output_dir is arbitrarily set, we assume
        # they're going to be the same for every run, set by one run_id
        ultron_jobs = [ultron_operator._build_job(inputs, rep_run_id)]
        job_name = ""
        job_input_json = ""
        self.assertEqual(1, len(ultron_jobs))  # there should only be one batch job; quirk that it must be in a list
        for ultron_job in ultron_jobs:
            if ultron_job.is_valid():
                job_name = ultron_job.name
                job_input_json = ultron_job.inputs
                tags = ultron_job.tags
                output_directory = ultron_job.output_directory
            expected_output_directory_with_timestamp = os.path.join(
                self.expected_output_directory, job_group.created_date.strftime("%Y%m%d_%H_%M_%f"), "analysis"
            )
            for key in job_input_json:
                self.assertEqual(ordered(job_input_json[key]), ordered(input_json[key]))
            self.assertEqual(output_directory, expected_output_directory_with_timestamp)

    def test_construct_inputs_obj_no_dmp_bams(self):
        """
        Test the creation of the inputs obj with no dmp bams
        """
        file_group_id = FileGroup.objects.get(name="DMP BAMs").pk
        files = FileRepository.filter(file_group=file_group_id)
        operator_model = Operator.objects.get(id=12)
        job_group = JobGroup()
        job_group.save()
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id
        )
        for single_file in files:
            single_file.delete()
        single_run_id = self.run_ids[0]
        sample_groups = ultron_operator._build_sample_groups([single_run_id])
        self.assertEqual(len(sample_groups[0]), 1)

    def test_construct_inputs_no_clinical_maf(self):
        """
        Test the created of the inputs obj with no mafs
        """
        file_group_id = FileGroup.objects.get(name="DMP Data Mutations Extended").pk
        files = FileRepository.filter(file_group=file_group_id)
        operator_model = Operator.objects.get(id=12)
        job_group = JobGroup()
        job_group.save()
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id
        )
        for single_file in files:
            single_file.delete()
        single_run_id = self.run_ids[0]
        sample_groups = ultron_operator._build_sample_groups([single_run_id])
        for sample_group in sample_groups:
            for item in sample_group:
                if item["sample_type"] == "clinical":
                    self.assertNotIn("maf_file", item)

    def test_construct_inputs_no_research_maf(self):
        """
        Test the created of the inputs obj with no mafs
        """
        runner_ports = Port.objects.filter(id__in=self.maf_runner_ports)
        for single_port in runner_ports:
            single_port.delete()
        operator_model = Operator.objects.get(id=12)
        job_group = JobGroup()
        job_group.save()
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id
        )
        single_run_id = self.run_ids[0]
        sample_groups = ultron_operator._build_sample_groups([single_run_id])
        for single_sample_group in sample_groups:
            for item in single_sample_group:
                if item["sample_type"] == "research":
                    self.assertNotIn("maf_file", item)

    def test_construct_sample_data_null_patient_id(self):
        """
        Test the creation of sample data with a null patient id
        """
        sample_metadata_1 = FileMetadata.objects.get(id=self.file_metadata_ids[0][0])
        sample_metadata_2 = FileMetadata.objects.get(id=self.file_metadata_ids[0][1])
        sample_id = sample_metadata_1.metadata[settings.SAMPLE_ID_METADATA_KEY]
        normal_id = sample_metadata_2.metadata[settings.SAMPLE_ID_METADATA_KEY]
        sample_metadata_1.metadata[settings.PATIENT_ID_METADATA_KEY] = None
        sample_metadata_1.save()
        sample_metadata_2.metadata[settings.PATIENT_ID_METADATA_KEY] = None
        sample_metadata_2.save()
        sample_data = SampleData(sample_id, normal_id)
        self.assertEqual(sample_data._get_dmp_patient_id(), None)
        self.assertEqual(sample_data._find_dmp_bams("T"), None)
        self.assertEqual(
            sample_data._get_sample_metadata(), (None, sample_metadata_1.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY])
        )

    def test_construct_sample_data_null_sample_name(self):
        """
        Test the creation of sample data with a null sample name
        """
        sample_metadata_1 = FileMetadata.objects.get(id=self.file_metadata_ids[0][0])
        sample_metadata_2 = FileMetadata.objects.get(id=self.file_metadata_ids[0][1])
        sample_id = sample_metadata_1.metadata[settings.SAMPLE_ID_METADATA_KEY]
        normal_id = sample_metadata_2.metadata[settings.SAMPLE_ID_METADATA_KEY]
        patient_id = sample_metadata_1.metadata[settings.PATIENT_ID_METADATA_KEY]
        sample_metadata_1.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = None
        sample_metadata_1.save()
        sample_metadata_2.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = None
        sample_metadata_2.save()
        sample_data = SampleData(sample_id, normal_id)
        self.assertEqual(sample_data._get_dmp_patient_id(), patient_id.lstrip("C-"))
        self.assertEqual(len(sample_data._find_dmp_bams("T")), 2)
        self.assertEqual(sample_data._get_sample_metadata(), (patient_id, None))

    def test_construct_sample_data(self):
        """
        Test the creation of sample data with a null sample name
        """
        sample_metadata_1 = FileMetadata.objects.get(id=self.file_metadata_ids[0][0])
        sample_metadata_2 = FileMetadata.objects.get(id=self.file_metadata_ids[0][1])
        sample_id = sample_metadata_1.metadata[settings.SAMPLE_ID_METADATA_KEY]
        normal_id = sample_metadata_2.metadata[settings.SAMPLE_ID_METADATA_KEY]
        patient_id = sample_metadata_1.metadata[settings.PATIENT_ID_METADATA_KEY]
        sample_data = SampleData(sample_id, normal_id)
        self.assertEqual(sample_data._get_dmp_patient_id(), patient_id.lstrip("C-"))
        self.assertEqual(len(sample_data._find_dmp_bams("T")), 2)
        self.assertEqual(
            sample_data._get_sample_metadata(),
            (patient_id, sample_metadata_1.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]),
        )

    def test_construct_bam_data(self):
        """
        Test the creation of bam data
        """
        single_bam = FileMetadata.objects.get(id=self.first_dmp_bam_metadata_id)
        bam_data = BamData(single_bam)
        self.assertEqual(bam_data._set_data_muts_txt(), self.first_dmp_mutations_extended)
        self.assertEqual(bam_data._set_dmp_sample_name(), self.first_dmp_dmp_sample_name)


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj
