"""
Tests for Roslin QC input parsing methods
"""
import os
import json
from uuid import UUID
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from file_system.models import File, FileMetadata, FileGroup
from runner.models import Run, Port, PortType
from runner.operator.roslin_qc_operator.bin.input import parse_outputs_files_data
from runner.operator.roslin_qc_operator.bin.input import parse_pairs_from_ports
from runner.operator.roslin_qc_operator.bin.input import parse_runparams_from_ports
from runner.operator.roslin_qc_operator.bin.input import get_db_files
from runner.operator.roslin_qc_operator.bin.input import get_baits_and_targets
from runner.operator.roslin_qc_operator.bin.input import build_inputs_from_runs
from runner.operator.roslin_qc_operator.bin.input import file_to_cwl
from runner.operator.roslin_qc_operator.bin.input import path_to_cwl
from runner.operator.roslin_qc_operator.bin.input import path_to_job_data
from runner.operator.roslin_qc_operator.bin.input import build_sample
from runner.operator.roslin_qc_operator.bin.input import pair_to_cwl
from runner.operator.roslin_qc_operator.bin.input import parse_bams_from_ports
from runner.operator.roslin_qc_operator.bin.input import file_to_job_data
from runner.operator.roslin_qc_operator.bin.input import pair_to_job_data

class TestInput(TestCase):
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json",
    "runner.pipeline.json",
    "beagle_etl.operator.json"
    ]

    def test_file_to_cwl1(self):
        """
        Test conversion of a File instance to an equivalent CWL entry

        """
        file_instance = File.objects.create(
            file_group = FileGroup.objects.first(),
            path = "/path/to/foo.txt")
        file_cwl = file_to_cwl(file_instance)
        expected_file_cwl = {'class': 'File', 'path': '/path/to/foo.txt'}
        self.assertEqual(file_cwl, expected_file_cwl)

        job_data = file_to_job_data(file_instance)
        expected_job_data = {'class': 'File', 'location': 'juno:///path/to/foo.txt'}
        self.assertEqual(job_data, expected_job_data)

    def test_path_to_cwl1(self):
        """
        Test conversion of a string based file path into CWL File format dict
        """
        file_cwl = path_to_cwl('/path/to/foo.txt')
        expected_file_cwl = {'class': 'File', 'path': '/path/to/foo.txt'}
        self.assertEqual(file_cwl, expected_file_cwl)

        job_data = path_to_job_data('/path/to/foo.txt')
        expected_job_data = {'class': 'File', 'location': 'juno:///path/to/foo.txt'}
        self.assertEqual(job_data, expected_job_data)

    def test_build_sample1(self):
        """
        Test building of the base dict datastructure to be used later in Roslin CWL output
        """
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        file_instance = File.objects.get(file_name = 'DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz')
        filemetadata_instance = FileMetadata.objects.filter(file = file_instance).order_by('-version').first()
        sample = build_sample(filemetadata_instance = filemetadata_instance)
        expected_sample = {'CN': 'MSKCC',
        'PL': 'Illumina',
        'PU': 'MyFlowCellId',
        'LB': 'MyLibraryId',
        'tumor_type': 'Tumor',
        'ID': 'C-ALLANT-T001-d_MyFlowCellId',
        'SM': 'C-ALLANT-T001-d',
        'species': 'Human',
        'patient_id': 'C-ALLANT',
        'bait_set': 'IMPACT468_BAITS',
        'igo_id': 'ALN-TEST-01',
        'run_date': None,
        'specimen_type': 'Blood',
        'request_id': 'ALN-REQ-ID'}
        self.assertEqual(sample, expected_sample)

    def test_parse_pairs_from_ports1(self):
        """
        Test that pairs are properly constructed from Port objects
        """
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        run_instance = Run.objects.first()
        ports = run_instance.port_set.all()
        pairs = parse_pairs_from_ports(ports)

        tumor_R2 = FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"))
        turmor_R1 = FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"))
        normal_R2 = FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"))
        normal_R1 = FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"))

        expected_pairs = [{
            'normal': {
                'R1': normal_R1,
                'R2': normal_R2
            },
            'tumor': {
                'R1': turmor_R1,
                'R2': tumor_R2
            }
        }]
        self.assertEqual(pairs, expected_pairs)

    def test_parse_bams_from_ports1(self):
        """
        Test that the 'bams' entries are constructed correctly from the Port objects
        """
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        run_instance = Run.objects.first()
        ports = run_instance.port_set.all()
        bams = parse_bams_from_ports(ports)
        expected_bams = {
        'normal_bam' : File.objects.get(file_name = 's_C_ALLANT_N002_d.rg.md.abra.printreads.bam'),
        'normal_bai' : File.objects.get(file_name = 's_C_ALLANT_N002_d.rg.md.abra.printreads.bai'),
        'tumor_bam' : File.objects.get(file_name = 's_C_ALLANT_T001_d.rg.md.abra.printreads.bam'),
        'tumor_bai' : File.objects.get(file_name = 's_C_ALLANT_T001_d.rg.md.abra.printreads.bai')
        }
        self.assertEqual(bams, expected_bams) # TODO: need to figure out how this will be handled; need the sample metadata associated with .bam files

    def test_pair_to_job_data(self):
        """
        Test that a pair dict is correctly converted to Job data for submission
        """
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        pair = {
            'normal': {
                'R1': FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz")),
                'R2': FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"))
            },
            'tumor': {
                'R1': FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz")),
                'R2': FileMetadata.objects.get(file = File.objects.get(file_name = "DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"))
            }
        }

        job_data = pair_to_job_data(pair)
        expected_job_data = ({
            "CN": "MSKCC",
            "PL": "Illumina",
            "PU": "MyFlowCellId",
            "LB": "MyLibraryId",
            "tumor_type": "Tumor",
            "ID": "C-ALLANT-T001-d_MyFlowCellId",
            "SM": "C-ALLANT-T001-d",
            "species": "Human",
            "patient_id": "C-ALLANT",
            "bait_set": "IMPACT468_BAITS",
            "igo_id": "ALN-TEST-01",
            "run_date": None,
            "specimen_type": "Blood",
            "request_id": "ALN-REQ-ID",
            "R1": {
                "class": "File",
                "location": "juno:///juno/work/pi/prototypes/register_fastqs/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R1_001.fastq.gz"
            },
            "R2": {
                "class": "File",
                "location": "juno:///juno/work/pi/prototypes/register_fastqs/DU874145-T/DU874145-T_IGO_00000_TEST_L001_R2_001.fastq.gz"
            }
        },
        {
            "CN": "MSKCC",
            "PL": "Illumina",
            "PU": "MyFlowCellId",
            "LB": "MyLibraryId",
            "tumor_type": "Normal",
            "ID": "C-ALLANT-N002-d_MyFlowCellId",
            "SM": "C-ALLANT-N002-d",
            "species": "Human",
            "patient_id": "C-ALLANT",
            "bait_set": "IMPACT468_BAITS",
            "igo_id": "ALN-TEST-02",
            "run_date": None,
            "specimen_type": "Blood",
            "request_id": "ALN-REQ-ID",
            "R1": {
                "class": "File",
                "location": "juno:///juno/work/pi/prototypes/register_fastqs/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R1_001.fastq.gz"
            },
            "R2": {
                "class": "File",
                "location": "juno:///juno/work/pi/prototypes/register_fastqs/DU874145-N/DU874145-N_IGO_00000_TEST_L001_R2_001.fastq.gz"
            }
        })

        self.assertEqual(job_data, expected_job_data)

    def test_parse_runparams_from_ports1(self):
        """
        Test that runparams are correctly parsed from Port queryset
        """
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        run_instance = Run.objects.first()
        ports = run_instance.port_set.all()
        runparams = parse_runparams_from_ports(ports)
        expected_runparams = {'genome': 'GRCh37',
            'pi': 'NA',
            'pi_email': 'NA',
            'project_prefix': 'ALN-REQ-ID',
            'scripts_bin': '/usr/bin',
            'assay': 'IMPACT468_BAITS'}
        self.assertEqual(runparams, expected_runparams)

    def test_get_baits_and_targets1(self):
        """
        Test that give a certain assay label, the correct one is returned
        """
        self.assertEqual(get_baits_and_targets("IMPACT468_BAITS"), "IMPACT468_b37")

    def test_get_db_files(self):
        """
        Test that db_files are returned correctly
        """
        assay = "IDT_Exome_v1_FP_b37"
        db_files = get_db_files(assay)
        expected_db_files = {
            'conpair_markers': '/usr/bin/conpair/data/markers/GRCh37.autosomes.phase3_shapeit2_mvncall_integrated.20130502.SNV.genotype.sselect_v4_MAF_0.4_LD_0.8.txt',
            'fp_genotypes': {
                'class': 'File',
                'location': 'juno:///juno/work/ci/resources/roslin_resources/targets/IDT_Exome_v1_FP/b37/FP_tiling_genotypes.txt'
            },
            'hotspot_list_maf': {
                'class': 'File',
                'location': 'juno:///juno/work/ci/resources/roslin-qc/hotspot-list-union-v1-v2.maf'
            },
            'ref_fasta': {
                'class': 'File',
                'location': 'juno:///juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta'
            }
        }
        self.assertEqual(db_files, expected_db_files)

    def test_parse_outputs_files_data1(self):
        """
        Test that a series of files are correctly organized into dict for QC input
        """
        files_data = [
        {'name': 'clstats1', 'file': {'class': 'File', 'path': '/path/to/clstats1.txt'} },
        {'name': 'clstats2', 'file': {'class': 'File', 'path': '/path/to/clstats2.txt'} },
        {'name': 'md_metrics', 'file': {'class': 'File', 'path': '/path/to/md_metrics.txt'} },
        {'name': 'hs_metrics', 'file': {'class': 'File', 'path': '/path/to/hs_metrics.txt'} },
        {'name': 'insert_metrics', 'file': {'class': 'File', 'path': '/path/to/insert_metrics.txt'} },
        {'name': 'per_target_coverage', 'file': {'class': 'File', 'path': '/path/to/per_target_coverage.txt'} },
        {'name': 'qual_metrics', 'file': {'class': 'File', 'path': '/path/to/qual_metrics.txt'} },
        {'name': 'doc_basecounts', 'file': {'class': 'File', 'path': '/path/to/doc_basecounts.txt'} },
        {'name': 'conpair_pileups', 'file': {'class': 'File', 'path': '/path/to/conpair_pileups.txt'} }
        ]
        qc_input = parse_outputs_files_data(files_data)
        expected_qc_input = {
        'clstats1': [{'class': 'File', 'path': '/path/to/clstats1.txt'}],
        'clstats2': [{'class': 'File', 'path': '/path/to/clstats2.txt'}],
        'md_metrics': [{'class': 'File', 'path': '/path/to/md_metrics.txt'}],
        'hs_metrics': [{'class': 'File', 'path': '/path/to/hs_metrics.txt'}],
        'insert_metrics': [{'class': 'File', 'path': '/path/to/insert_metrics.txt'}],
        'per_target_coverage': [{'class': 'File', 'path': '/path/to/per_target_coverage.txt'}],
        'qual_metrics': [{'class': 'File', 'path': '/path/to/qual_metrics.txt'}],
        'doc_basecounts': [{'class': 'File', 'path': '/path/to/doc_basecounts.txt'}],
        'conpair_pileups': [{'class': 'File', 'path': '/path/to/conpair_pileups.txt'}],
        }
        self.assertEqual(qc_input, expected_qc_input)


    def test_build_inputs_from_run_and_ports1(self):
        """
        Test generation of Roslin QC input from Roslin pipeline output Run and Port instances
        """
        # load test pipeline Run output fixtures
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "dfefc47b-3ee4-4867-890f-9bab87c7f53f.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        run_queryset = Run.objects.all()

        qc_input = build_inputs_from_runs(run_queryset)
        # print(">>> printing qc_input to file")
        # print(json.dumps(qc_input, indent = 4), file = open("qc_input.json", 'w'))

        # TODO: how to test output format?
        self.assertEqual(len(qc_input['pairs']), 2)
        self.assertEqual(len(qc_input['pairs'][0]), 2)
        self.assertEqual(len(qc_input['bams']), 2)
        self.assertEqual(len(qc_input['bams'][0]), 2)

    def test_load_extra_fixtures(self):
        """
        Sanity test to ensure that our fixtures have not changed
        """
        self.assertEqual(len(Run.objects.all()),  0)
        self.assertEqual(len(Port.objects.all()),  0)
        self.assertEqual(len(File.objects.all()),  0)
        self.assertEqual(len(FileMetadata.objects.all()),  0)

        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "aa0694f1-0109-4205-a6b2-63e3e1d7c0a2.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        self.assertEqual(len(Run.objects.all()),  1)
        self.assertEqual(len(Port.objects.all()),  51)
        self.assertEqual(len(File.objects.all()),  114)
        self.assertEqual(len(FileMetadata.objects.all()),  114)

        test_files_fixture = os.path.join(settings.FIXTURES_DIR, "runs", "dfefc47b-3ee4-4867-890f-9bab87c7f53f.run.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        self.assertEqual(len(Run.objects.all()),  2)
        self.assertEqual(len(Port.objects.all()),  102)
        self.assertEqual(len(File.objects.all()),  168)
        self.assertEqual(len(FileMetadata.objects.all()),  168)
