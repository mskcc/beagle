import copy
import os
import csv
import logging
from django.db.models import Q
from django.conf import settings
from beagle import __version__
from datetime import datetime
from runner.operator.operator import Operator
from runner.models import Pipeline
from notifier.models import JobGroup
from file_system.repository.file_repository import FileRepository
import runner.operator.chronos_operator.bin.tempo_patient as patient_obj
from notifier.events import OperatorRequestEvent, ChronosMissingSamplesEvent
from notifier.tasks import send_notification
from runner.run.objects.run_creator_object import RunCreator

LOGGER = logging.getLogger(__name__)
DESTINATION_DIRECTORY = "/data1/core006/tempo/wes_repo/Results/v2.0.x/bams"


class ChronosOperator(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.1.0"

    def build_recipe_query(self):
        """
        Build complex Q object assay query from given data
        Only does OR queries, as seen in line
           query |= item
        Very similar to build_assay_query, but "metadata__recipe"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_recipes()
        data_query_set = [Q(("metadata__{}".format(settings.RECIPE_METADATA_KEY), value)) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query

    def build_assay_query(self):
        """
        Build complex Q object assay query from given data
        Only does OR queries, as seen in line
           query |= item
        Very similar to build_recipe_query, but "metadata__baitSet"
        can't be sent as a value, so had to make a semi-redundant function
        """
        data = self.get_assays()
        data_query_set = [Q(metadata__baitSet=value) for value in set(data)]
        query = data_query_set.pop()
        for item in data_query_set:
            query |= item
        return query

    def filter_out_missing_fields_query(self):
        """
        This is for legacy purposes - if FileMetadata don't contain sampleTy[e or ciTag,
        remove them from the file set
        """
        query = Q(("metadata__{}__isnull".format(settings.CMO_SAMPLE_TAG_METADATA_KEY), False)) & Q(
            ("metadata__{}__isnull".format(settings.CMO_SAMPLE_CLASS_METADATA_KEY), False)
        )
        return query

    def get_jobs(self, pairing_override=None):
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = pipeline.output_directory
        self.OUTPUT_DIR = output_directory
        recipe_query = self.build_recipe_query()
        assay_query = self.build_assay_query()
        igocomplete_query = Q(metadata__igoComplete=True)
        missing_fields_query = self.filter_out_missing_fields_query()
        q = recipe_query & assay_query & igocomplete_query & missing_fields_query
        tempo_files = FileRepository.filter(queryset=FileRepository.all(), q=q, file_group=self.file_group)
        tempo_files = FileRepository.filter(queryset=tempo_files, filter_redact=True)

        self.send_message(
            """
            Querying database for the following recipes:
                {recipes}

            Querying database for the following assays/bait sets:
                {assays}
            """.format(
                recipes="\t\n".join(self.get_recipes()), assays="\t\n".join(self.get_assays())
            )
        )

        exclude_query = self.get_exclusions()
        if exclude_query:
            tempo_files = tempo_files.exclude(exclude_query)
        # replace with run operator logic, most recent pairing
        pre_pairing = dict()
        if pairing_override:
            normal_samples = pairing_override["normal_samples"]
            tumor_samples = pairing_override["tumor_samples"]
            num_ns = len(normal_samples)
            num_ts = len(tumor_samples)
            if num_ns != num_ts:
                print("Number of tumors and normals not the same; can't pair")
            else:
                for i in range(0, num_ns):
                    tumor_id = tumor_samples[i]
                    normal_id = normal_samples[i]
                    pre_pairing[tumor_id] = normal_id
        patient_ids = set()
        patient_files = dict()
        no_patient_samples = list()
        for entry in tempo_files:
            patient_id = entry.metadata[settings.PATIENT_ID_METADATA_KEY]
            if patient_id:
                patient_ids.add(patient_id)
                if patient_id not in patient_files:
                    patient_files[patient_id] = list()
                patient_files[patient_id].append(entry)
            else:
                no_patient_samples.append(entry)

        self.patients = dict()
        self.non_cmo_patients = dict()
        for patient_id in patient_files:
            if "C-" in patient_id[:2]:
                self.patients[patient_id] = patient_obj.Patient(patient_id, patient_files[patient_id], pre_pairing)
            else:
                patient_file = patient_files[patient_id][0]
                specimen_type = patient_file.metadata[settings.SAMPLE_CLASS_METADATA_KEY]
                if "cellline" in specimen_type.lower():
                    self.patients[patient_id] = patient_obj.Patient(patient_id, patient_files[patient_id], pre_pairing)
                else:
                    self.non_cmo_patients[patient_id] = patient_obj.Patient(patient_id, patient_files[patient_id])

        mapping_all = self.create_mapping_input()
        pairing_all = self.create_pairing_input()

        mapping = dict()
        beagle_version = __version__
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        tags = {
            "beagle_version": beagle_version,
            "run_date": run_date,
        }

        if not self.pairing:
            pairing_for_request = []
            tumors = FileRepository.filter(
                metadata={
                    settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                },
                file_group=self.file_group,
                values_metadata=settings.CMO_SAMPLE_TAG_METADATA_KEY,
            )
            used_normals = set()
            used_normals_requests = set()
            unpaired_tumors = set()

            for tumor in tumors:
                pairing = self.get_pairing_for_sample(tumor, pairing_all)
                if pairing:
                    pairing_for_request.append(pairing)
                    mapping = self.get_mapping_for_pair(tumor, pairing["normal"], mapping_all, used_normals)
                    normal_request_id = FileRepository.filter(
                        metadata={settings.SAMPLE_ID_METADATA_KEY: pairing["normal"]},
                        file_group=self.file_group,
                        values_metadata=settings.REQUEST_ID_METADATA_KEY,
                    )
                    used_normals_requests.add(normal_request_id)
                else:
                    unpaired_tumors.add(tumor)
                    mapping = self.get_mapping_for_unpaired_tumor(tumor, mapping_all)

                if unpaired_tumors:
                    self.send_message(
                        """
                        Unpaired tumors in mapping file:
                        {tumors}
                        """.format(
                            tumors="\t\n".join(list(unpaired_tumors))
                        )
                    )
        else:
            for pair in self.pairing.get("pairs"):
                tumor_sample = self.get_ci_tag(pair["tumor"])
                normal_sample = self.get_ci_tag(pair["normal"])
                if tumor_sample:
                    sample_map = self.get_mapping_for_sample(tumor_sample, mapping_all)
                    mapping[tumor_sample] = sample_map
                if normal_sample:
                    sample_map = self.get_mapping_for_sample(normal_sample, mapping_all)
                    mapping[normal_sample] = sample_map

        jobs = []
        missing_samples = set()
        for sample, files in mapping.items():
            check_bam_path = os.path.join(DESTINATION_DIRECTORY, f"{sample}", f"{sample}.bam")
            if os.path.exists(check_bam_path):
                LOGGER.info(f"{sample} already generated, {check_bam_path} exist. Skip")
                continue
            name = "Tempo Run {sample_id}: {run_date}".format(sample_id=sample, run_date=run_date)
            output_directory = os.path.join(
                self.OUTPUT_DIR,
                self.CHRONOS_NAME,
                self.request_id,
                sample,
                self.CHRONOS_VERSION,
                jg_created_date,
            )
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
            input_json = {
                "mapping": files,
                "somatic": False,
                "aggregate": False,
                "workflows": "qc",
                "assayType": "exome",
            }
            if self.missing_fastqs(files):
                missing_samples.add(sample)
                continue
            patient_id = FileRepository.filter(
                metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample},
                file_group=self.file_group,
                values_metadata=settings.PATIENT_ID_METADATA_KEY,
            ).first()
            request_id = FileRepository.filter(
                metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample},
                file_group=self.file_group,
                values_metadata=settings.REQUEST_ID_METADATA_KEY,
            ).first()
            gene_panel = FileRepository.filter(
                metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample},
                file_group=self.file_group,
                values_metadata=settings.RECIPE_METADATA_KEY,
            ).first()
            primary_id = FileRepository.filter(
                metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample},
                file_group=self.file_group,
                values_metadata=settings.SAMPLE_ID_METADATA_KEY,
            ).first()
            job_tags = copy.deepcopy(tags)
            job_tags.update(
                {
                    settings.PATIENT_ID_METADATA_KEY: patient_id,
                    settings.SAMPLE_ID_METADATA_KEY: primary_id,
                    settings.REQUEST_ID_METADATA_KEY: request_id,
                    settings.RECIPE_METADATA_KEY: gene_panel,
                    settings.CMO_SAMPLE_TAG_METADATA_KEY: sample,
                }
            )
            job_json = {
                "name": name,
                "app": app,
                "inputs": input_json,
                "tags": job_tags,
                "output_directory": output_directory,
                "output_metadata": {
                    "pipeline": pipeline.name,
                    "pipeline_version": pipeline.version,
                    settings.PATIENT_ID_METADATA_KEY: patient_id,
                    settings.SAMPLE_ID_METADATA_KEY: primary_id,
                    settings.REQUEST_ID_METADATA_KEY: request_id,
                    settings.RECIPE_METADATA_KEY: gene_panel,
                    settings.CMO_SAMPLE_TAG_METADATA_KEY: sample,
                },
            }
            jobs.append(job_json)
        if missing_samples:
            missing_samples_event = ChronosMissingSamplesEvent(
                job_notifier=self.job_group_id, samples=", ".join(list(missing_samples))
            )
            send_notification.delay(missing_samples_event.to_dict())
        return [RunCreator(**job) for job in jobs]

    def get_pairing_for_sample(self, tumor, pairing):
        for p in pairing:
            if p["tumor"] == tumor:
                return p

    def get_mapping_for_pair(self, tumor, normal, mapping, used_normals):
        map = dict()
        map[tumor] = []
        map[normal] = []
        for m in mapping:
            if m["sample"] == tumor:
                map[tumor].append(m)
            if m["sample"] == normal:
                map[normal].append(m)
                if normal not in used_normals:
                    used_normals.add(normal)
        return map

    def get_mapping_for_sample(self, sample_id, mapping):
        result = []
        for m in mapping:
            if m["sample"] == sample_id:
                result.append(m)
        return result

    def get_mapping_for_unpaired_tumor(self, tumor, mapping):
        map = dict()
        map[tumor] = []
        for m in mapping:
            if m["sample"] == tumor:
                map[tumor].append(m)
        return map

    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_notifier_id, msg)
        e = event.to_dict()
        send_notification.delay(e)

    def get_recipes(self):
        recipe = [
            "WES_Human",
            "WES_HUMAN",
            "Agilent_v4_51MB_Human",
            "IDT_Exome_v1_FP",
            "WholeExomeSequencing",
            "IDT_Exome_v1_FP_Viral_Probes",
            "IDT_Exome_v2_FP_Viral_Probes",
        ]
        return recipe

    def get_assays(self):
        assays = [
            "Agilent_v4_51MB_Human_hg19_BAITS",
            "IDT_Exome_v1_FP_b37_baits",
            "IDT_Exome_v1_FP_BAITS",
            "IDT_Exome_v2_FP_b37_baits",
            "IDT_Exome_v2_GRCh38_BAITS",
            "SureSelect-All-Exon-V4-hg19",
            "IDT_Exome_v2_BAITS",
            "IDT_Exome_v2_FP_BAITS",
        ]
        return assays

    def create_mapping_input(self):
        mapping = []
        for patient_id in self.patients:
            patient = self.patients[patient_id]
            mapping.extend(patient.create_mapping_json_all_samples_included())
        return mapping

    def create_pairing_input(self):
        pairing_json = []
        for patient_id in self.patients:
            pairing_json.extend(self.patients[patient_id].create_pairing_json())
        return pairing_json

    def exclude_requests(self, l):
        q = None
        for i in l:
            if q:
                q |= Q(("metadata__{}".format(settings.REQUEST_ID_METADATA_KEY), i))
            else:
                q = Q(("metadata__{}".format(settings.REQUEST_ID_METADATA_KEY), i))
        return q

    def get_exclusions(self):
        exclude_reqs = ["09315"]
        return self.exclude_requests(exclude_reqs)

    def get_ci_tag(self, primary_id):
        return FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: primary_id},
            file_group=self.file_group,
            values_metadata=settings.CMO_SAMPLE_TAG_METADATA_KEY,
        ).first()

    def missing_fastqs(self, files):
        for f in files:
            if not f["fastq_pe1"] or not f["fastq_pe2"]:
                return True

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
