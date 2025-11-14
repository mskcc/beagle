import os
import copy
import logging
from django.conf import settings
from beagle import __version__
from datetime import datetime
from runner.operator.operator import Operator
from runner.models import Pipeline
from notifier.models import JobGroup
from file_system.repository.file_repository import FileRepository
from notifier.events import OperatorRequestEvent, ChronosMissingSamplesEvent
from notifier.tasks import send_notification
from runner.run.objects.run_creator_object import RunCreator

LOGGER = logging.getLogger(__name__)
DESTINATION_DIRECTORY = "/data1/core006/tempo/wes_repo/Results/v2.0.x/bams"


class ChronosOperatorV2(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.2.0"

    RECIPES = [
        "WES_Human",
        "WES_HUMAN",
        "Agilent_v4_51MB_Human",
        "IDT_Exome_v1_FP",
        "WholeExomeSequencing",
        "IDT_Exome_v1_FP_Viral_Probes",
        "IDT_Exome_v2_FP_Viral_Probes",
    ]

    ASSAYS = [
        "Agilent_v4_51MB_Human_hg19_BAITS",
        "IDT_Exome_v1_FP_b37_baits",
        "IDT_Exome_v1_FP_BAITS",
        "IDT_Exome_v2_FP_b37_baits",
        "IDT_Exome_v2_GRCh38_BAITS",
        "SureSelect-All-Exon-V4-hg19",
        "IDT_Exome_v2_BAITS",
        "IDT_Exome_v2_FP_BAITS",
    ]

    def validate_sample(self, sample, files):
        valid = True
        message = f"{sample}"
        for f in files:
            if f.metadata["igoComplete"] == False:
                valid = False
                message += f" not igoComplete"
            if not f.metadata[settings.RECIPE_METADATA_KEY] in self.RECIPES:
                valid = False
                message += f" not supported genePanel:{settings.RECIPE_METADATA_KEY}"
            if not f.metadata[settings.BAITSET_METADATA_KEY] in self.ASSAYS:
                valid = False
                message += f" not supported baitSet:{settings.BAITSET_METADATA_KEY}"
            if not f.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]:
                valid = False
                message += f" no {settings.CMO_SAMPLE_TAG_METADATA_KEY}"
        if valid:
            message += " valid"
        return valid, message

    def construct_job(self, sample, fastqs, pipeline, tags, run_date, jg_created_date):
        """
        {
            "mapping": [
                {
                    "sample": "sample_id",
                    "target": "idt",
                    "fastq_pe1": {
                        "class": "File",
                        "location": "juno:///path/to/fastq_R1.fastq.gz"
                    },
                    "fastq_pe2": {
                        "class": "File",
                        "location": "juno:///path/to/fastq_R2.fastq.gz"
                    },
                    "num_fq_pairs": 1
                }
            ]
        }
        """
        name = "Tempo Run {sample_id}: {run_date}".format(sample_id=sample, run_date=run_date)
        ci_tag = self.get_ci_tag(sample)
        bait_set = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: sample},
            file_group=self.file_group,
            file_type="fastq",
            values_metadata=settings.BAITSET_METADATA_KEY,
        ).first()
        target = self._resolve_target(bait_set)
        output_directory = os.path.join(
            self.OUTPUT_DIR,
            self.CHRONOS_NAME,
            self.request_id,
            ci_tag,
            self.CHRONOS_VERSION,
            jg_created_date,
        )
        fastq_pairs = self.pair_samples(fastqs)
        mapping = []
        num_of_fastq_pairs = len(fastq_pairs)
        for fq_pair in fastq_pairs:
            mapping.append(
                {
                    "sample": ci_tag,
                    "target": target,
                    "fastq_pe1": {"class": "File", "location": f"iris://{fq_pair[0].file.path}"},
                    "fastq_pe2": {"class": "File", "location": f"iris://{fq_pair[1].file.path}"},
                    "num_fq_pairs": num_of_fastq_pairs,
                }
            )
        input_json = {
            "mapping": mapping,
            "somatic": False,
            "aggregate": False,
            "workflows": "qc",
            "assayType": "exome",
        }
        patient_id = FileRepository.filter(
            metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: ci_tag},
            file_group=self.file_group,
            values_metadata=settings.PATIENT_ID_METADATA_KEY,
        ).first()
        request_id = FileRepository.filter(
            metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: ci_tag},
            file_group=self.file_group,
            values_metadata=settings.REQUEST_ID_METADATA_KEY,
        ).first()
        gene_panel = FileRepository.filter(
            metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: ci_tag},
            file_group=self.file_group,
            values_metadata=settings.RECIPE_METADATA_KEY,
        ).first()
        job_tags = copy.deepcopy(tags)
        job_tags.update(
            {
                settings.PATIENT_ID_METADATA_KEY: patient_id,
                settings.SAMPLE_ID_METADATA_KEY: sample,
                settings.REQUEST_ID_METADATA_KEY: request_id,
                settings.RECIPE_METADATA_KEY: gene_panel,
                settings.CMO_SAMPLE_TAG_METADATA_KEY: ci_tag,
            }
        )
        job_json = {
            "name": name,
            "app": str(pipeline.id),
            "inputs": input_json,
            "tags": job_tags,
            "output_directory": output_directory,
            "output_metadata": {
                "pipeline": pipeline.name,
                "pipeline_version": pipeline.version,
                settings.PATIENT_ID_METADATA_KEY: patient_id,
                settings.SAMPLE_ID_METADATA_KEY: sample,
                settings.REQUEST_ID_METADATA_KEY: request_id,
                settings.RECIPE_METADATA_KEY: gene_panel,
                settings.CMO_SAMPLE_TAG_METADATA_KEY: ci_tag,
            },
        }
        return job_json

    def pair_samples(self, fastqs):
        """
        pair sample fastqs based on the delivery directory.

        Parameters:
            fastqs (list): A list of sample fastq files.

        Returns:
            list: A list of tuples containing paired fastqs for a sample
        """
        sample_pairs = []
        expected_pair = set(["R1", "R2"])
        # match R1 and R2 based on delivery directory
        # sorting on file names is not enough as they are non-unique
        for i, fastq in enumerate(fastqs):
            dir = "/".join(fastq.file.path.split("_R")[0:-1])
            for compare in fastqs[i + 1 :]:
                compare_dir = "/".join(compare.file.path.split("_R")[0:-1])
                if dir == compare_dir:
                    # check if R1 and R2 are present
                    r_check = set([fastq.metadata["R"], compare.metadata["R"]])
                    if r_check.issubset(expected_pair):
                        # Keep ordering consistent
                        if fastq.metadata["R"] == "R1":
                            sample_pairs.append((fastq, compare))
                        else:
                            sample_pairs.append((compare, fastq))
                    else:
                        sample_name = fastq.metadata["cmoSampleName"]
                        raise Exception(f"Improper pairing for: {sample_name}")
        return sample_pairs

    def _resolve_target(self, bait_set):
        """ """
        target_assay = bait_set.lower()
        if "agilent" in target_assay:
            return "agilent"
        if "idt" in target_assay:
            if "v2" in target_assay:
                return "idt_v2"
            return "idt"
        if "sureselect" in target_assay:
            return "agilent"
        return None

    def _get_bait_sets(self):
        bait_sets = set()
        for value in self.metadata["baitSet"]:
            bait_set = self._resolve_target(value)
            bait_sets.add(bait_set)
        return bait_sets

    def get_jobs_for_samples(self, samples, pipeline, tags, run_date, jg_created_date):
        jobs = []
        for sample in samples:
            fastqs = FileRepository.filter(
                metadata={settings.SAMPLE_ID_METADATA_KEY: sample}, file_group=self.file_group, file_type="fastq"
            )
            valid, message = self.validate_sample(sample, fastqs)
            if valid:
                jobs.append(self.construct_job(sample, fastqs, pipeline, tags, run_date, jg_created_date))
            else:
                self.send_message(message)
        return jobs

    def get_jobs(self, pairing_override=None):
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = pipeline.output_directory
        self.OUTPUT_DIR = output_directory
        beagle_version = __version__
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        tags = {
            "beagle_version": beagle_version,
            "run_date": run_date,
        }

        if not self.pairing:
            samples = FileRepository.filter(
                metadata={
                    settings.REQUEST_ID_METADATA_KEY: self.request_id,
                },
                file_group=self.file_group,
                values_metadata=settings.SAMPLE_ID_METADATA_KEY,
            ).all()
            samples = list(samples)
        else:
            samples = set()
            for pair in self.pairing.get("pairs"):
                if pair["tumor"]:
                    samples.add(pair["tumor"])
                if pair["normal"]:
                    samples.add(pair["normal"])
            samples = list(samples)
            self.request_id = FileRepository.filter(
                metadata={settings.SAMPLE_ID_METADATA_KEY: samples[0]},
                file_group=self.file_group,
                values_metadata=settings.REQUEST_ID_METADATA_KEY,
            ).first()

        samples_to_process = []
        for sample in samples:
            ci_tag = self.get_ci_tag(sample)
            check_bam_path = os.path.join(DESTINATION_DIRECTORY, f"{ci_tag}", f"{ci_tag}.bam")
            if os.path.exists(check_bam_path):
                LOGGER.info(f"{sample} already generated, {check_bam_path} exist. Skip")
                continue
            samples_to_process.append(sample)

        jobs = self.get_jobs_for_samples(samples_to_process, pipeline, tags, run_date, jg_created_date)
        return [RunCreator(**job) for job in jobs]

    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_notifier_id, msg)
        e = event.to_dict()
        send_notification.delay(e)

    def get_ci_tag(self, primary_id):
        return FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: primary_id},
            file_group=self.file_group,
            values_metadata=settings.CMO_SAMPLE_TAG_METADATA_KEY,
        ).first()

    def get_log_directory(self):
        pipeline = Pipeline.objects.get(id=self.get_pipeline_id())
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        log_directory = os.path.join(
            pipeline.log_directory,
            self.CHRONOS_NAME,
            self.request_id,
            self.CHRONOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return log_directory
