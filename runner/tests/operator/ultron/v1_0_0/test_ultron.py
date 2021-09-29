"""
Test for constructing ultron inputs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.ultron.v1_0_0.phase1 import UltronOperator, InputsObj, SampleData, BamData
from beagle_etl.models import Operator
from notifier.models import JobGroup
from runner.models import Run
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
        os.environ['TMPDIR'] = ''
        self.run_ids = ["28ca34e8-9d4c-4543-9fc7-981bf5f6a97f",
                        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59"]
        self.sample_ids = [["9af6ab44-0117-479c-aeab-d7a774f4c9b9", "f750a0a2-5fe5-440c-a7d4-e042fe3c470c"],
                           ["0ef3577f-e57e-4e99-82b2-efc96c41032e", "f750a0a2-5fe5-440c-a7d4-e042fe3c470c"]]
        self.file_metadata_ids = [[
            "c28794bf-de45-40a1-b32f-5659263ddde3",
            "969b2757-c116-4569-b39f-0294335dfea8",
            "d769789b-7938-4ac5-b897-121d7623c61a",
            "6226e750-ba7a-4144-a9d4-835e93dc31ea"

        ], ["c53b78d4-3b13-4029-8dbc-bfa5f254c515",
            "d769789b-7938-4ac5-b897-121d7623c61a",
            "6226e750-ba7a-4144-a9d4-835e93dc31ea",
            "b8142135-a50f-4090-b5e4-0f92587c9a96"]]
        self.first_dmp_bam_metadata_id = "638dbd71-0d7d-46bb-833d-25b7d90651c7"
        self.first_dmp_mutations_extended_id = "92a88d6d-92cc-4107-a334-d11c75efd8d6"
        self.first_dmp_mutations_extended = "/path/to/P-0000000-T01-IM6.txt"
        self.first_dmp_dmp_sample_name = "s_REDACTED"
        self.first_run_expected_inputs = {'unindexed_bam_files': [{'class': 'File', 'location': 'juno:///path/to/00000001-T.bam'}, {'class': 'File', 'location': 'juno:///path/to/P-00000002-T.bam'}], 'unindexed_sample_ids': ['s_REDACTED', 's_REDACTED'], 'unindexed_maf_files': [{'class': 'File', 'location': 'juno:///path/to/P-0000000-T01-IM6.txt'}, {'class': 'File', 'location': 'juno:///path/to/P-0000002-T01-IM6.txt'}], 'maf_files': [{'class': 'File', 'location': 'juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.s_C_ALLANT_N002_d.muts.maf'}], 'bam_files': [
            {'class': 'File', 'location': 'juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.rg.md.abra.printreads.bam', 'secondaryFiles': [{'class': 'File', 'location': 'juno:///juno/work/ci/voyager-output/28ca34e8-9d4c-4543-9fc7-981bf5f6a97f/s_C_ALLANT_T003_d.rg.md.abra.printreads.bai'}]}], 'sample_ids': ['s_C_ALLANT_T003_d'], 'ref_fasta': {'class': 'File', 'location': 'juno:///juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta'}, 'exac_filter': {'class': 'File', 'location': 'juno:///juno/work/ci/resources/vep/cache/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz'}}
        self.expected_output_directory = "/juno/work/pi/beagle/output/argos_pair_sv/argos/ALN-REQ-ID/1.0.0-rc5/"
        self.expected_project_prefix = "ALN-REQ-ID"

    def test_construct_output_directory(self):
        """
        Test the creation of the output directory and project prefix tag
        """
        job_group = JobGroup()
        job_group.save()
        operator_model = Operator.objects.get(id=12)
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id)
        ultron_operator._get_output_directory(self.run_ids)
        expected_output_directory_with_timestamp = os.path.join(
            self.expected_output_directory, job_group.created_date.strftime("%Y%m%d_%H_%M_%f"))
        self.assertEqual(ultron_operator.output_directory,
                         expected_output_directory_with_timestamp)
        self.assertEqual(ultron_operator.project_prefix,
                         self.expected_project_prefix)

    def test_construct_ultron_job(self):
        """
        Test the creation of an ultron job
        """
        sample = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][0]).metadata["sampleId"]
        input_json = {"sample_ids": [sample]}
        ultron_run_name = "Sample %s ULTRON PHASE1 run" % sample
        operator_model = Operator.objects.get(id=12)
        job_group = JobGroup()
        job_group.save()
        ultron_operator = UltronOperator(
            operator_model, pipeline="cb5d793b-e650-4b7d-bfcd-882858e29cc5", job_group_id=job_group.id)
        ultron_operator._get_output_directory(self.run_ids)
        ultron_job = ultron_operator._build_job(input_json)
        job_name = ""
        job_input_json = ""
        if ultron_job[0].is_valid():
            job_name = ultron_job[0].data['name']
            job_input_json = ultron_job[0].data['inputs']
            tags = ultron_job[0].data['tags']
            output_directory = ultron_job[0].data['output_directory']
        expected_output_directory_with_timestamp = os.path.join(
            self.expected_output_directory, job_group.created_date.strftime("%Y%m%d_%H_%M_%f"))
        self.assertEqual(job_name, ultron_run_name)
        self.assertEqual(job_input_json, input_json)
        self.assertEqual(tags['project_prefix'], self.expected_project_prefix)
        self.assertEqual(output_directory,
                         expected_output_directory_with_timestamp)

    def test_construct_inputs_obj_no_dmp_bams(self):
        """
        Test the creation of the inputs obj with no dmp bams
        """
        file_group_id = FileGroup.objects.get(name="DMP BAMs").pk
        files = FileRepository.filter(file_group=file_group_id)
        for single_file in files:
            single_file.delete()
        single_run = Run.objects.get(id=self.run_ids[0])
        input_obj = InputsObj(single_run)
        input_json = input_obj._build_inputs_json()
        self.assertEqual(input_json["unindexed_bam_files"],
                         [])
        self.assertEqual(input_json["unindexed_sample_ids"],
                         [])
        self.assertEqual(input_json["unindexed_maf_files"],
                         [])

    def test_construct_inputs_obj_no_dmp_muts(self):
        """
        Test the creation of the inputs obj with no dmp muts
        """
        file_group_id = FileGroup.objects.get(
            name="DMP Data Mutations Extended").pk
        files = FileRepository.filter(file_group=file_group_id)
        for single_file in files:
            single_file.delete()
        single_run = Run.objects.get(id=self.run_ids[0])
        input_obj = InputsObj(single_run)
        expected_input_json = self.first_run_expected_inputs
        input_json = input_obj._build_inputs_json()
        self.assertEqual(input_json['unindexed_maf_files'], [])

    def test_construct_inputs_obj(self):
        """
        Test the creation of the inputs obj
        """
        single_run = Run.objects.get(id=self.run_ids[0])
        input_obj = InputsObj(single_run)
        input_json = input_obj._build_inputs_json()
        self.assertEqual(len(input_json["unindexed_bam_files"]),
                         2)
        self.assertEqual(len(input_json["unindexed_sample_ids"]),
                         2)
        self.assertEqual(len(input_json["unindexed_maf_files"]),
                         2)
        self.assertEqual(len(input_json["bam_files"]),
                         1)
        self.assertEqual(len(input_json["sample_ids"]),
                         1)
        self.assertEqual(len(input_json["ref_fasta"]),
                         2)
        self.assertEqual(len(input_json["exac_filter"]),
                         2)

    def test_construct_sample_data_null_patient_id(self):
        """
        Test the creation of sample data with a null patient id
        """
        sample_metadata_1 = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][0])
        sample_metadata_2 = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][1])
        sample_id = sample_metadata_1.metadata["sampleId"]
        sample_metadata_1.metadata["patientId"] = None
        sample_metadata_1.save()
        sample_metadata_2.metadata["patientId"] = None
        sample_metadata_2.save()
        sample_data = SampleData(sample_id)
        self.assertEqual(sample_data._get_dmp_patient_id(), None)
        self.assertEqual(sample_data._find_dmp_bams("T"), None)
        self.assertEqual(sample_data._get_sample_metadata(),
                         (None, sample_metadata_1.metadata["cmoSampleName"]))

    def test_construct_sample_data_null_sample_name(self):
        """
        Test the creation of sample data with a null sample name
        """
        sample_metadata_1 = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][0])
        sample_metadata_2 = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][1])
        sample_id = sample_metadata_1.metadata["sampleId"]
        patient_id = sample_metadata_1.metadata["patientId"]
        sample_metadata_1.metadata["cmoSampleName"] = None
        sample_metadata_1.save()
        sample_metadata_2.metadata["cmoSampleName"] = None
        sample_metadata_2.save()
        sample_data = SampleData(sample_id)
        self.assertEqual(sample_data._get_dmp_patient_id(),
                         patient_id.lstrip('C-'))
        self.assertEqual(len(sample_data._find_dmp_bams("T")), 2)
        self.assertEqual(sample_data._get_sample_metadata(),
                         (patient_id, None))

    def test_construct_sample_data(self):
        """
        Test the creation of sample data with a null sample name
        """
        sample_metadata_1 = FileMetadata.objects.get(
            id=self.file_metadata_ids[0][0])
        sample_id = sample_metadata_1.metadata["sampleId"]
        patient_id = sample_metadata_1.metadata["patientId"]
        sample_data = SampleData(sample_id)
        self.assertEqual(sample_data._get_dmp_patient_id(),
                         patient_id.lstrip('C-'))
        self.assertEqual(len(sample_data._find_dmp_bams("T")), 2)
        self.assertEqual(sample_data._get_sample_metadata(),
                         (patient_id, sample_metadata_1.metadata["cmoSampleName"]))

    def test_construct_bam_data_missing_muts(self):
        """
        Test the creation of bam data when the mutation files are missing
        """
        single_bam = FileMetadata.objects.get(
            id=self.first_dmp_bam_metadata_id)
        mutation_file = FileMetadata.objects.get(
            id=self.first_dmp_mutations_extended_id)
        mutation_file.delete()
        bam_data = BamData(single_bam)
        self.assertEqual(bam_data._set_data_muts_txt(),
                         [])
        self.assertEqual(bam_data._set_dmp_sample_name(),
                         self.first_dmp_dmp_sample_name)

    def test_construct_bam_data(self):
        """
        Test the creation of bam data
        """
        single_bam = FileMetadata.objects.get(
            id=self.first_dmp_bam_metadata_id)
        bam_data = BamData(single_bam)
        self.assertEqual(bam_data._set_data_muts_txt(),
                         self.first_dmp_mutations_extended)
        self.assertEqual(bam_data._set_dmp_sample_name(),
                         self.first_dmp_dmp_sample_name)
