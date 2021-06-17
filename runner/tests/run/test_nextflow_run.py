import json
from mock import patch
from rest_framework.test import APITestCase
from runner.run.objects.nextflow.nextflow_run_object import NextflowRunObject
from runner.run.objects.nextflow.nextflow_port_object import NextflowPortObject
from runner.models import Run, ProtocolType, RunStatus, Pipeline, PortType, Port
from file_system.models import FileGroup, File, FileType, FileExtension


class NextflowRunObjectTest(APITestCase):

    def setUp(self):
        self.nxf_file_group = FileGroup.objects.create(name='Nextflow Output Group')
        self.pipeline = Pipeline.objects.create(
            name='nextflow_pipeline',
            github='https://github.com/nextflow_pipeline',
            version='1.0.0',
            entrypoint='pipeline.nf',
            output_file_group=self.nxf_file_group,
            output_directory='/output/directory/',
            config="TEST CONFIG"
        )
        self.fastq_type = FileType.objects.create(name='fastq')
        self.fastq_ext = FileExtension.objects.create(extension='fastq',
                                                      file_type=self.fastq_type)
        self.file_1 = File.objects.create(path='/path/to/file_1.fastq',
                                          file_group=self.nxf_file_group)
        self.file_2 = File.objects.create(path='/path/to/file_2.fastq',
                                          file_group=self.nxf_file_group)
        self.file_a_1 = File.objects.create(path='/path/to/file_a_1.fastq',
                                          file_group=self.nxf_file_group)
        self.file_a_2 = File.objects.create(path='/path/to/file_a_2.fastq',
                                          file_group=self.nxf_file_group)
        self.file_b_1 = File.objects.create(path='/path/to/file_b_1.fastq',
                                          file_group=self.nxf_file_group)
        self.file_b_2 = File.objects.create(path='/path/to/file_b_2.fastq',
                                          file_group=self.nxf_file_group)

    @patch('runner.pipeline.pipeline_cache.PipelineCache.get_pipeline')
    def test_port_from_definition(self, get_pipeline):
        with open('runner/tests/run/inputs.template.json', 'r') as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/file_1.fastq"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/file_2.fastq"
                    }
                }
            ]
        }
        run = Run.objects.create(app=self.pipeline,
                                 run_type=ProtocolType.NEXTFLOW,
                                 name='Nextflow Run 1',
                                 status=RunStatus.CREATING,
                                 notify_for_outputs=[])
        port_object = NextflowPortObject.from_definition(str(run.id),
                                                         inputs['inputs'][0],
                                                         PortType.INPUT,
                                                         input_dict)
        port_object.ready()
        port_object.to_db()
        port = Port.objects.get(name="mapping")
        template_value = """SAMPLE\tASSAY\tTARGET\tFASTQ_PE1\tFASTQ_PE2
sample_id\tassay_value\ttarget_value\t/path/to/file_1.fastq\t/path/to/file_2.fastq
"""
        self.assertEqual(port.value, template_value)

    @patch('runner.pipeline.pipeline_cache.PipelineCache.get_pipeline')
    def test_run_from_definition(self, get_pipeline):
        with open('runner/tests/run/inputs.template.json', 'r') as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id_a",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/file_a_1.fastq"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/file_a_2.fastq"
                    }
                },
                {
                    "sample": "sample_id_b",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/file_b_1.fastq"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/file_b_2.fastq"
                    }
                }
            ],
            "pairing": [
                {
                    "tumor": "TUMOR_1",
                    "normal": "NORMAL_1"
                }
            ]
        }
        run = Run.objects.create(app=self.pipeline,
                                 run_type=ProtocolType.NEXTFLOW,
                                 name='Nextflow Run 1',
                                 status=RunStatus.CREATING,
                                 notify_for_outputs=[])
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        run_object.to_db()
        run.refresh_from_db()
        mapping = Port.objects.get(name="mapping")
        template_value_mapping = """SAMPLE\tASSAY\tTARGET\tFASTQ_PE1\tFASTQ_PE2
sample_id_a\tassay_value\ttarget_value\t/path/to/file_a_1.fastq\t/path/to/file_a_2.fastq
sample_id_b\tassay_value\ttarget_value\t/path/to/file_b_1.fastq\t/path/to/file_b_2.fastq
"""
        pairing = Port.objects.get(name="pairing")
        template_value_pairing = """NORMAL_ID\tTUMOR_ID
NORMAL_1\tTUMOR_1
"""
        self.assertEqual(mapping.value, template_value_mapping)
        self.assertEqual(pairing.value, template_value_pairing)
        self.assertEqual(run.status, RunStatus.READY)

        run_from_db = NextflowRunObject.from_db(str(run.id))
        self.assertEqual(run_from_db.run_type, ProtocolType.NEXTFLOW)
        self.assertEqual(len(run_from_db.inputs), 3)
        self.assertEqual(len(run_from_db.outputs), 1)

    @patch('runner.pipeline.pipeline_cache.PipelineCache.get_pipeline')
    def test_run_dump_job(self, get_pipeline):
        with open('runner/tests/run/inputs.template.json', 'r') as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id_a",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/file_a_1.fastq"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/file_a_2.fastq"
                    }
                },
                {
                    "sample": "sample_id_b",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/file_b_1.fastq"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/file_b_2.fastq"
                    }
                }
            ],
            "pairing": [
                {
                    "tumor": "TUMOR_1",
                    "normal": "NORMAL_1"
                }
            ]
        }
        run = Run.objects.create(app=self.pipeline,
                                 run_type=ProtocolType.NEXTFLOW,
                                 name='Nextflow Run 1',
                                 status=RunStatus.CREATING,
                                 notify_for_outputs=[])
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        job_json = run_object.dump_job()
        self.assertEqual(job_json['type'], 1)
        self.assertEqual(job_json['app'], {
            'github': {'repository': 'https://github.com/nextflow_pipeline', 'entrypoint': 'pipeline.nf',
                       'version': '1.0.0'}})
        self.assertEqual(job_json['inputs']['config'], 'TEST CONFIG')
        self.assertEqual(len(job_json['inputs']['inputs']), 2)
        self.assertEqual(len(job_json['inputs']['params']), 1)
        self.assertEqual(job_json['inputs']['profile'], 'juno')
