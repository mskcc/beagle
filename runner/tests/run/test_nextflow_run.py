import json
from mock import patch
from rest_framework.test import APITestCase
from runner.run.objects.nextflow.nextflow_run_object import NextflowRunObject
from runner.run.objects.nextflow.nextflow_port_object import NextflowPortObject
from runner.models import Run, ProtocolType, RunStatus, Pipeline, PortType, Port, Sample
from file_system.models import FileGroup, File, FileType, FileExtension
from runner.pipeline.pipeline_cache import PipelineCache


class NextflowRunObjectTest(APITestCase):
    def setUp(self):
        self.nxf_file_group = FileGroup.objects.create(name="Nextflow Output Group")
        self.pipeline = Pipeline.objects.create(
            name="nextflow_pipeline",
            github="https://github.com/nextflow_pipeline",
            version="1.0.0",
            entrypoint="pipeline.nf",
            output_file_group=self.nxf_file_group,
            output_directory="/output/directory/",
            config="TEST CONFIG",
            profiles=["juno"],
        )
        self.pipeline_nf = Pipeline.objects.create(
            name="nextflow_pipeline",
            github="https://github.com/nf-core/taxprofiler.git",
            version="master",
            entrypoint="pipeline.nf",
            output_file_group=self.nxf_file_group,
            output_directory="/output/directory/",
            config="TEST CONFIG",
            nfcore_template=True,
            pipeline_type=ProtocolType.NEXTFLOW,
            profiles=["singularity"],
        )
        config = """process {\r\n  memory = \"8.GB\"\r\n  time = { task.attempt < 3 ? 3.h * task.attempt  : 500.h }\r\n  clusterOptions = \"\"\r\n  scratch = true\r\n  beforeScript = \". \/etc\/profile.d\/modules.sh; module load singularity\/3.1.1; unset R_LIBS; catch_term () { echo 'caught USR2\/TERM signal'; set +e; false; on_exit ; } ; trap catch_term USR2 TERM\"\r\n}\r\n\r\nparams {\r\n  fileTracking = \"{{output_directory}}\"\r\n}"""
        self.pipeline_config = Pipeline.objects.create(
            name="nextflow_pipeline_config",
            github="https://github.com/nextflow_pipeline",
            version="1.0.0",
            entrypoint="pipeline.nf",
            output_file_group=self.nxf_file_group,
            output_directory="/output/directory/",
            config=config,
            profiles=["juno"],
        )
        self.fastq_type = FileType.objects.create(name="fastq")
        self.fastq_ext = FileExtension.objects.create(extension="fastq", file_type=self.fastq_type)
        self.sample_tumor = Sample.objects.create(
            sample_id="SAMPLE-TUMOR-001",
            sample_name="P-SAMPLE-TUMOR-001-WES",
            cmo_sample_name="C_SAMPLE_TUMOR_001",
            sample_type="Metastasis",
            tumor_or_normal="Tumor",
            sample_class="Blood",
        )
        self.sample_normal = Sample.objects.create(
            sample_id="SAMPLE-NORMAL-001",
            sample_name="P-SAMPLE-NORMAL-001-WES",
            cmo_sample_name="C_SAMPLE_NORMAL_001",
            sample_type="Normal",
            tumor_or_normal="Normal",
            sample_class="Blood",
        )
        self.file_1 = File.objects.create(path="/path/to/file_1.fastq", file_group=self.nxf_file_group)
        self.file_2 = File.objects.create(path="/path/to/file_2.fastq", file_group=self.nxf_file_group)
        self.file_db = File.objects.create(path="/path/to/db.tar.gz", file_group=self.nxf_file_group)
        self.file_db.save()
        self.file_a_1 = File.objects.create(path="/path/to/file_a_1.fastq", file_group=self.nxf_file_group)
        self.file_a_1.samples.append(self.sample_tumor.sample_id)
        self.file_a_1.save()
        self.file_a_2 = File.objects.create(path="/path/to/file_a_2.fastq", file_group=self.nxf_file_group)
        self.file_a_2.samples.append(self.sample_tumor.sample_id)
        self.file_a_2.save()
        self.file_b_1 = File.objects.create(path="/path/to/file_b_1.fastq", file_group=self.nxf_file_group)
        self.file_b_1.samples.append(self.sample_normal.sample_id)
        self.file_b_1.save()
        self.file_b_2 = File.objects.create(path="/path/to/file_b_2.fastq", file_group=self.nxf_file_group)
        self.file_b_2.samples.append(self.sample_normal.sample_id)
        self.file_b_2.save()

    def test_get_pipeline_nf(self):

        input_dict = {
            "input": [
                {
                    "sample": "2612",
                    "run_accession": "ERR5766176",
                    "instrument_platform": "ILLUMINA",
                    "target": "target_value",
                    "fastq_1": {"class": "File", "location": "juno:///path/to/file_a_1.fastq"},
                    "fastq_2": {"class": "File", "location": "juno:///path/to/file_a_2.fastq"},
                    "fasta": "",
                }
            ],
            "databases": [
                {
                    "tool": "malt",
                    "db_name": "malt85",
                    "db_params": "-id 85",
                    "db_type": "short",
                    "db_path": {"class": "File", "location": "juno:///path/to/db.tar.gz"},
                }
            ],
        }

        run = Run.objects.create(
            app=self.pipeline_nf,
            run_type=ProtocolType.NEXTFLOW,
            name="Nextflow Run 1",
            status=RunStatus.CREATING,
            notify_for_outputs=[],
        )
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        run_object.to_db()
        job_json = run_object.dump_job()
        self.assertEqual(len(job_json["inputs"]["inputs"]), 2)
        self.assertEqual(
            job_json["inputs"]["inputs"][0]["content"],
            "sample,run_accession,instrument_platform,fastq_1,fastq_2,fasta\n2612,ERR5766176,ILLUMINA,/path/to/file_a_1.fastq,/path/to/file_a_2.fastq,\n",
        )
        self.assertEqual(
            job_json["inputs"]["inputs"][1]["content"],
            "tool,db_name,db_params,db_type,db_path\nmalt,malt85,-id 85,short,/path/to/db.tar.gz\n",
        )
        self.assertEqual(job_json["inputs"]["profile"], "singularity")

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_port_from_definition(self, get_pipeline):
        with open("runner/tests/run/inputs.template.json", "r") as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_2.fastq"},
                }
            ]
        }
        run = Run.objects.create(
            app=self.pipeline,
            run_type=ProtocolType.NEXTFLOW,
            name="Nextflow Run 1",
            status=RunStatus.CREATING,
            notify_for_outputs=[],
        )
        port_object = NextflowPortObject.from_definition(str(run.id), inputs["inputs"][0], PortType.INPUT, input_dict)
        port_object.ready()
        port_object.to_db()
        port = Port.objects.get(name="mapping")
        template_value = """SAMPLE\tASSAY\tTARGET\tFASTQ_PE1\tFASTQ_PE2
sample_id\tassay_value\ttarget_value\t/path/to/file_1.fastq\t/path/to/file_2.fastq
"""
        self.assertEqual(port.value, template_value)

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_run_from_definition(self, get_pipeline):
        with open("runner/tests/run/inputs.template.json", "r") as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "SAMPLE-TUMOR-001",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_a_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_a_2.fastq"},
                },
                {
                    "sample": "SAMPLE-NORMAL-001",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_b_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_b_2.fastq"},
                },
            ],
            "pairing": [{"tumor": "SAMPLE-TUMOR-001", "normal": "SAMPLE-NORMAL-001"}],
        }
        run = Run.objects.create(
            app=self.pipeline,
            run_type=ProtocolType.NEXTFLOW,
            name="Nextflow Run 1",
            status=RunStatus.CREATING,
            notify_for_outputs=[],
        )
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        run_object.to_db()
        run.refresh_from_db()
        mapping = Port.objects.get(name="mapping")
        template_value_mapping = """SAMPLE\tASSAY\tTARGET\tFASTQ_PE1\tFASTQ_PE2
SAMPLE-TUMOR-001\tassay_value\ttarget_value\t/path/to/file_a_1.fastq\t/path/to/file_a_2.fastq
SAMPLE-NORMAL-001\tassay_value\ttarget_value\t/path/to/file_b_1.fastq\t/path/to/file_b_2.fastq
"""
        pairing = Port.objects.get(name="pairing")
        template_value_pairing = """NORMAL_ID\tTUMOR_ID
SAMPLE-NORMAL-001\tSAMPLE-TUMOR-001
"""
        self.assertEqual(mapping.value, template_value_mapping)
        self.assertEqual(pairing.value, template_value_pairing)
        self.assertEqual(run.status, RunStatus.READY)

        run_from_db = NextflowRunObject.from_db(str(run.id))
        self.assertEqual(run_from_db.run_type, ProtocolType.NEXTFLOW)
        self.assertEqual(len(run_from_db.inputs), 3)
        self.assertEqual(len(run_from_db.outputs), 1)
        self.assertEqual(len(run_from_db.samples), 2)

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_run_dump_job(self, get_pipeline):
        with open("runner/tests/run/inputs.template.json", "r") as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id_a",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_a_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_a_2.fastq"},
                },
                {
                    "sample": "sample_id_b",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_b_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_b_2.fastq"},
                },
            ],
            "pairing": [{"tumor": "TUMOR_1", "normal": "NORMAL_1"}],
        }
        run = Run.objects.create(
            app=self.pipeline,
            run_type=ProtocolType.NEXTFLOW,
            name="Nextflow Run 1",
            status=RunStatus.CREATING,
            notify_for_outputs=[],
        )
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        job_json = run_object.dump_job()
        self.assertEqual(job_json["type"], 1)
        self.assertEqual(
            job_json["app"],
            {
                "github": {
                    "repository": "https://github.com/nextflow_pipeline",
                    "entrypoint": "pipeline.nf",
                    "version": "1.0.0",
                    "nfcore_template": False,
                }
            },
        )
        self.assertEqual(job_json["inputs"]["config"], "TEST CONFIG")
        self.assertEqual(len(job_json["inputs"]["inputs"]), 2)
        self.assertEqual(len(job_json["inputs"]["params"]), 1)
        self.assertEqual(job_json["inputs"]["profile"], "juno")

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_config(self, get_pipeline):
        with open("runner/tests/run/inputs.template.json", "r") as f:
            inputs = json.load(f)
        get_pipeline.return_value = inputs
        input_dict = {
            "mapping": [
                {
                    "sample": "sample_id_a",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_a_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_a_2.fastq"},
                },
                {
                    "sample": "sample_id_b",
                    "assay": "assay_value",
                    "target": "target_value",
                    "fastq_pe1": {"class": "File", "location": "juno:///path/to/file_b_1.fastq"},
                    "fastq_pe2": {"class": "File", "location": "juno:///path/to/file_b_2.fastq"},
                },
            ],
            "pairing": [{"tumor": "TUMOR_1", "normal": "NORMAL_1"}],
        }
        run = Run.objects.create(
            app=self.pipeline_config,
            run_type=ProtocolType.NEXTFLOW,
            name="Nextflow Run 1",
            status=RunStatus.CREATING,
            notify_for_outputs=[],
        )
        run_object = NextflowRunObject.from_definition(str(run.id), input_dict)
        run_object.ready()
        job_json = run_object.dump_job(output_directory="/tmp/test/output")
        self.assertEqual(job_json["inputs"]["outputs"], "/tmp/test/output/pipeline_output.csv")
        self.assertTrue("/tmp/test/output/pipeline_output.csv" in job_json["inputs"]["config"])
