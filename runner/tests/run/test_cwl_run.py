import json
import uuid
from mock import patch
from django.db import transaction
from rest_framework.test import APITestCase
from runner.models import Port
from runner.tasks import complete_job, fail_job
from runner.models import Run, RunStatus, Pipeline, OperatorRun
from runner.run.processors.file_processor import FileProcessor
from runner.run.objects.run_object_factory import RunObjectFactory
from beagle_etl.models import JobGroup
from file_system.models import Storage, StorageType, FileGroup, File, FileType, Sample, Request


class CWLRunObjectTest(APITestCase):
    fixtures = [
        "beagle_etl.operator.json",
        "runner.operator_run.json",
        "runner.operator_trigger.json",
    ]

    def setUp(self):
        self.storage = Storage(name="test", type=StorageType.LOCAL)
        self.storage.save()
        self.file_group = FileGroup(name="Test Files", storage=self.storage)
        self.file_group.save()
        self.pipeline = Pipeline(
            name="pipeline_name",
            github="http://pipeline.github.com",
            version="v1.0",
            entrypoint="pipeline.cwl",
            output_file_group=self.file_group,
            output_directory="/path/to/outputs",
        )
        self.pipeline.save()
        self.run = Run(run_type=0, app=self.pipeline, status=RunStatus.CREATING, notify_for_outputs=[])
        self.run.save()
        self.file_type_unknown = FileType(name="unknown")
        self.file_type_unknown.save()
        self.request = Request.objects.create(request_id="REQUEST_1")
        self.sample_1 = Sample.objects.create(sample_id="SAMPLE_1", sample_name="SAMPLE_NAME_1", request_id="REQUEST_1")
        self.sample_2 = Sample.objects.create(sample_id="SAMPLE_2", sample_name="SAMPLE_NAME_2", request_id="REQUEST_1")
        self.file1 = File(
            **{
                "file_name": "FASTQ_L002_R1_001.fastq.gz",
                "path": "/FASTQ/FASTQ_L002_R1_001.fastq.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
                "samples": ["SAMPLE_1"],
            }
        )
        self.file1.save()
        self.file2 = File(
            **{
                "file_name": "FASTQ_L002_R2_001.fastq.gz",
                "path": "/FASTQ/FASTQ_L002_R2_001.fastq.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
                "samples": ["SAMPLE_1"],
            }
        )
        self.file2.save()
        self.file3 = File(
            **{
                "file_name": "FASTQ_L006_R1_001.fastq.gz",
                "path": "/FASTQ/FASTQ_L006_R1_001.fastq.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
                "samples": ["SAMPLE_2"],
            }
        )
        self.file3.save()
        self.file4 = File(
            **{
                "file_name": "FASTQ_L006_R2_001.fastq.gz",
                "path": "/FASTQ/FASTQ_L006_R2_001.fastq.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
                "samples": ["SAMPLE_2"],
            }
        )
        self.file4.save()
        file_list = [
            {
                "file_name": "GRCm38.fasta",
                "path": "/resources/genomes/GRCm38/GRCm38.fasta",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "b37.fasta",
                "path": "/resources/genomes/GRCh37/fasta/b37.fasta",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "hapmap_3.3.b37.vcf",
                "path": "/resources/request_files/hapmap/hapmap_3.3.b37.vcf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "dbsnp_137.b37__RmDupsClean__plusPseudo50__DROP_SORT.vcf.gz",
                "path": "/resources/genomes/GRCh37/facets_snps/dbsnp_137.b37__RmDupsClean__plusPseudo50__DROP_SORT.vcf.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "human.hg19.excl.tsv",
                "path": "/resources/genomes/GRCh37/delly/human.hg19.excl.tsv",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "hotspot-list-union-v1-v2.maf",
                "path": "/resources/qc_resources/hotspot-list-union-v1-v2.maf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "AgilentExon_v2_FP_tiling_intervals.intervals",
                "path": "/resources/genomic_resources/targets/AgilentExon_v2/b37/AgilentExon_v2_FP_tiling_intervals.intervals",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "AgilentExon_v2_FP_tiling_genotypes.txt",
                "path": "/resources/genomic_resources/targets/AgilentExon_v2/b37/AgilentExon_v2_FP_tiling_genotypes.txt",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "AgilentExon_v2_b37_baits.ilist",
                "path": "/resources/genomic_resources/targets/AgilentExon_v2/b37/AgilentExon_v2_b37_baits.ilist",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "AgilentExon_v2_b37_targets.ilist",
                "path": "/resources/genomic_resources/targets/AgilentExon_v2/b37/AgilentExon_v2_b37_targets.ilist",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "refGene_b37.sorted.txt",
                "path": "/resources/request_files/refseq/refGene_b37.sorted.txt",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz",
                "path": "/resources/vep/cache/ExAC_nonTCGA.r0.3.1.sites.vep.vcf.gz",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "CosmicCodingMuts_v67_b37_20131024__NDS.vcf",
                "path": "/resources/request_files/cosmic/CosmicCodingMuts_v67_b37_20131024__NDS.vcf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "s_C_006537_N001_d.Group0.rg.md.abra.printreads.bam",
                "path": "/resources/curated_bams/IDT_Exome_v1_FP_b37/s_C_006537_N001_d.Group0.rg.md.abra.printreads.bam",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "s_C_006284_N002_d.Group3.rg.md.abra.printreads.bam",
                "path": "/resources/curated_bams/IDT_Exome_v1_FP_b37/s_C_006284_N002_d.Group3.rg.md.abra.printreads.bam",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "Mills_and_1000G_gold_standard.indels.b37.vcf",
                "path": "/resources/request_files/indels_1000g/Mills_and_1000G_gold_standard.indels.b37.vcf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "dbsnp_138.b37.excluding_sites_after_129.vcf",
                "path": "/resources/request_files/dbsnp/dbsnp_138.b37.excluding_sites_after_129.vcf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
            {
                "file_name": "1000G_phase1.snps.high_confidence.b37.vcf",
                "path": "/resources/request_files/snps_1000g/1000G_phase1.snps.high_confidence.b37.vcf",
                "size": 1234,
                "file_group": self.file_group,
                "file_type": self.file_type_unknown,
            },
        ]
        for f in file_list:
            self.file = File(**f)
            self.file.save()
        self.outputs = {
            "maf": {
                "size": 68273211,
                "class": "File",
                "nameext": ".maf",
                "basename": "test_1.muts.maf",
                "checksum": "sha1$0ccf4718a717f5a991607561af0b5bf989caf1e4",
                "location": "file:///outputs/test_1.muts.maf",
                "nameroot": "test_1.muts.maf",
            },
            "normal_bam": [
                {
                    "size": 56524168530,
                    "class": "File",
                    "nameext": ".bam",
                    "basename": "test_1.printreads.bam",
                    "checksum": "sha1$e4c05e8b3e7c1d682640e690f71536e22cb63802",
                    "location": "file:///output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_1.rg.md.abra.printreads.bam",
                    "nameroot": "test_1.printreads.bam",
                    "secondaryFiles": [
                        {
                            "size": 7214992,
                            "class": "File",
                            "nameext": ".bai",
                            "basename": "test_1.rg.md.abra.printreads.bai",
                            "checksum": "sha1$79299d55657a0226206a4bf3ddaba854ae11f9f1",
                            "location": "file:///output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_1.rg.md.abra.printreads.bai",
                            "nameroot": "test_1.rg.md.abra.printreads.bai",
                        }
                    ],
                }
            ],
            "tumor_bam": [
                {
                    "size": 6163808009,
                    "class": "File",
                    "nameext": ".bam",
                    "basename": "test_2.rg.md.abra.printreads.bam",
                    "checksum": "sha1$15ddc908c3ece551d331e78806d3ac19569174c3",
                    "location": "file:///output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_2.rg.md.abra.printreads.bam",
                    "nameroot": "test_2.rg.md.abra.printreads",
                    "secondaryFiles": [
                        {
                            "size": 6235920,
                            "class": "File",
                            "nameext": ".bai",
                            "basename": "test_2.rg.md.abra.printreads.bai",
                            "checksum": "sha1$6fd2fc0ce6b42253cbac89d31e8eddb169d65605",
                            "location": "file:///output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_2.rg.md.abra.printreads.bai",
                            "nameroot": "test_2.rg.md.abra.printreads",
                        }
                    ],
                },
            ],
        }

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_run_creation_from_cwl(self, mock_get_pipeline):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)
        mock_get_pipeline.return_value = app
        run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        run.ready()
        for inp in run.inputs:
            if inp.name == "pair":
                self.assertEqual(inp.db_value[0]["R1"][0]["location"], "bid://%s" % str(self.file1.id))
                self.assertEqual(inp.value[0]["R1"][0]["path"], self.file1.path)
                self.assertEqual(inp.db_value[0]["R2"][0]["location"], "bid://%s" % str(self.file2.id))
                self.assertEqual(inp.value[0]["R2"][0]["path"], self.file2.path)
                self.assertEqual(inp.db_value[1]["R1"][0]["location"], "bid://%s" % str(self.file3.id))
                self.assertEqual(inp.value[1]["R1"][0]["path"], self.file3.path)
                self.assertEqual(inp.db_value[1]["R2"][0]["location"], "bid://%s" % str(self.file4.id))
                self.assertEqual(inp.value[1]["R2"][0]["path"], self.file4.path)
        self.assertTrue(self.sample_1 in run.samples)
        self.assertTrue(self.sample_2 in run.samples)

    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    def test_run_to_db(self, mock_get_pipeline):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)
        mock_get_pipeline.return_value = app
        run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        run.to_db()
        try:
            run_obj = Run.objects.get(id=run.run_id)
        except Run.DoesNotExist as e:
            pass
        self.assertEqual(str(run_obj.id), run.run_id)

    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_run_complete_job(
        self, mock_populate_job_group_notifier, mock_get_pipeline, memcache_task_lock, send_notification
    ):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)
        mock_populate_job_group_notifier.return_value = None
        mock_get_pipeline.return_value = app
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        job_group = JobGroup.objects.create()
        run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        run.job_group = job_group
        run.to_db()
        run.ready()
        operator_run = OperatorRun.objects.first()
        operator_run.runs.add(run.run_obj)
        num_completed_runs = operator_run.num_completed_runs
        complete_job(run.run_id, self.outputs)
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.num_completed_runs, num_completed_runs + 1)
        run_obj = RunObjectFactory.from_db(run.run_id)
        file_obj = File.objects.filter(path=self.outputs["maf"]["location"].replace("file://", "")).first()
        run_obj.to_db()
        for out in run_obj.outputs:
            if out.name == "maf":
                self.assertEqual(out.value["location"], self.outputs["maf"]["location"])
                self.assertEqual(FileProcessor.get_bid_from_file(file_obj), out.db_value["location"])
        port1 = Port.objects.filter(run_id=run_obj.run_id, name="normal_bam").first()
        port2 = Port.objects.filter(run_id=run_obj.run_id, name="tumor_bam").first()
        self.assertEqual(len(port1.files.all()), 2)
        self.assertEqual(len(port2.files.all()), 2)
        expected_result = (
            "/output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_1.rg.md.abra.printreads.bam",
            "/output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_1.rg.md.abra.printreads.bai",
            "/output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_2.rg.md.abra.printreads.bam",
            "/output/argos_pair_workflow/425194f6-a974-4c2f-995f-f27d7ba54ddc/outputs/test_2.rg.md.abra.printreads.bai",
        )
        self.assertTrue(port1.files.all()[0].path in expected_result)
        self.assertTrue(port1.files.all()[1].path in expected_result)
        self.assertTrue(port2.files.all()[0].path in expected_result)
        self.assertTrue(port2.files.all()[1].path in expected_result)

    @patch("runner.models.Run.set_for_restart")
    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    @patch("runner.tasks._job_finished_notify")
    def test_run_fail_job(
        self, job_finished_notify, mock_get_pipeline, memcache_task_lock, send_notification, set_for_restart
    ):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)

        job_finished_notify.return_value = None
        set_for_restart.return_value = None
        mock_get_pipeline.return_value = app
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        run.to_db()

        operator_run = OperatorRun.objects.first()
        operator_run.runs.add(run.run_obj)
        num_failed_runs = operator_run.num_failed_runs
        fail_job(run.run_id, {"details": "Error has happened"})
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.num_failed_runs, num_failed_runs + 1)

        run_obj = RunObjectFactory.from_db(run.run_id)
        self.assertEqual(run_obj.message, {"details": "Error has happened"})

    @patch("runner.models.Run.set_for_restart")
    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    @patch("runner.tasks._job_finished_notify")
    def test_multiple_failed_on_same_job(
        self, job_finished_notify, mock_get_pipeline, memcache_task_lock, send_notification, set_for_restart
    ):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)

        job_finished_notify.return_value = None
        set_for_restart.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        mock_get_pipeline.return_value = app
        run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        run.to_db()

        operator_run = OperatorRun.objects.first()
        operator_run.runs.add(run.run_obj)
        num_failed_runs = operator_run.num_failed_runs
        fail_job(run.run_id, {"details": "Error has happened"})
        fail_job(run.run_id, {"details": "Error has happened"})
        fail_job(run.run_id, {"details": "Error has happened"})
        operator_run.refresh_from_db()
        self.assertEqual(operator_run.num_failed_runs, num_failed_runs + 1)

    @patch("runner.tasks._upload_qc_report")
    @patch("runner.tasks.submit_job")
    @patch("notifier.tasks.send_notification.delay")
    @patch("lib.memcache_lock.memcache_task_lock")
    @patch("runner.pipeline.pipeline_cache.PipelineCache.get_pipeline")
    @patch("runner.tasks._job_finished_notify")
    def test_resume_and_restart(
        self,
        job_finished_notify,
        mock_get_pipeline,
        memcache_task_lock,
        send_notification,
        submit_job,
        _upload_qc_report,
    ):
        with open("runner/tests/run/pair-workflow.cwl", "r") as f:
            app = json.load(f)
        with open("runner/tests/run/inputs.json", "r") as f:
            inputs = json.load(f)

        job_finished_notify.return_value = None
        memcache_task_lock.return_value = True
        send_notification.return_value = False
        mock_get_pipeline.return_value = app
        submit_job.return_value = None
        _upload_qc_report.return_value = None
        cwl_run = RunObjectFactory.from_definition(str(self.run.id), inputs)
        cwl_run.to_db()
        run = cwl_run.run_obj
        run_uuid = uuid.uuid4()
        run.execution_id = run_uuid
        run.resume_attempts = 2
        run.restart_attempts = 3
        run.save()
        fail_job(run.pk, {"details": "Error has happened"})
        _, _, execution_id = run.set_for_restart()
        self.assertEqual(execution_id, run_uuid)
        self.assertTrue(run.message["initial"] != None)
        fail_job(run.pk, {"details": "Error has happened"})
        run.execution_id = run_uuid
        run.save()
        _, _, execution_id = run.set_for_restart()
        self.assertEqual(execution_id, run_uuid)
        self.assertTrue(len(run.message["resume"]) == 1)
        fail_job(run.pk, {"details": "Error has happened"})
        _, _, execution_id = run.set_for_restart()
        self.assertEqual(execution_id, None)
        self.assertTrue(len(run.message["resume"]) == 2)
        fail_job(run.pk, {"details": "Error has happened"})
        _, _, execution_id = run.set_for_restart()
        self.assertEqual(execution_id, None)
        self.assertTrue(len(run.message["restart"]) == 1)
        fail_job(run.pk, {"details": "Error has happened"})
        _, _, execution_id = run.set_for_restart()
        self.assertEqual(execution_id, None)
        self.assertTrue(len(run.message["restart"]) == 2)
        fail_job(run.pk, {"details": "Error has happened"})
        restart_output = run.set_for_restart()
        self.assertEqual(restart_output, None)
        self.assertTrue(len(run.message["restart"]) == 2)
