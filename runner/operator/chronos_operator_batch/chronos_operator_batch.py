import os
import json
import csv
import logging
import unicodedata
from django.db.models import Q
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.models import File, FileGroup, FileType
from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.models import Pipeline
import runner.operator.chronos_operator_batch.bin.tempo_patient as patient_obj
from notifier.models import JobGroup
from notifier.events import OperatorRequestEvent
from notifier.tasks import send_notification
from runner.run.objects.run_creator_object import RunCreator

LOGGER = logging.getLogger(__name__)


class ChronosOperatorBatch(Operator):
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
        files = FileRepository.filter(filter_redact=True)
        tempo_files = FileRepository.filter(queryset=files, q=q)
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

        beagle_version = __version__
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        tags = {"beagle_version": beagle_version, "run_date": run_date}
        jobs = []
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        output_directory = os.path.join(
            output_directory, self.CHRONOS_NAME, self.request_id, self.CHRONOS_VERSION, jg_created_date
        )

        name = f"Tempo Run requestId:{self.request_id} {run_date}"

        pairing_for_request = []
        mapping_for_request = []
        tumors = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: self.request_id, "tumorOrNormal": "Tumor"},
            values_metadata="ciTag",
        )
        used_normals = set()
        used_normals_requests = set()
        unpaired_tumors = set()

        for tumor in tumors:
            pairing = self.get_pairing_for_sample(tumor, pairing_all)
            if pairing:
                pairing_for_request.append(pairing)
                mapping_for_request.extend(
                    self.get_mapping_for_sample(tumor, pairing["normal"], mapping_all, used_normals)
                )
                normal_request_id = FileRepository.filter(
                    metadata={settings.SAMPLE_ID_METADATA_KEY: pairing["normal"]},
                    values_metadata=settings.REQUEST_ID_METADATA_KEY,
                )
                used_normals_requests.add(normal_request_id)
            else:
                unpaired_tumors.add(tumor)
                mapping_for_request.extend(self.get_mapping_for_unpaired_tumor(tumor, mapping_all))

        if unpaired_tumors:
            self.send_message(
                """
                Unpaired tumors in mapping file:
                {tumors}
                """.format(
                    tumors="\t\n".join(list(unpaired_tumors))
                )
            )

        if self.request_id in used_normals_requests:
            used_normals_requests.remove(self.request_id)

        if used_normals_requests:
            LOGGER.info(f"Normals from different requests {','.join(map(str,list(used_normals_requests)))}.")

        input_json = {
            "mapping": mapping_for_request,
            "somatic": False,
            "aggregate": False,
            "workflows": "qc",
            "assayType": "exome",
        }

        job_json = {"name": name, "app": app, "inputs": input_json, "tags": tags, "output_directory": output_directory}
        jobs.append(job_json)
        return [RunCreator(**job) for job in jobs]

    def get_pairing_for_sample(self, tumor, pairing):
        for p in pairing:
            if p["tumor"] == tumor:
                return p

    def get_mapping_for_sample(self, tumor, normal, mapping, used_normals):
        map = []
        for m in mapping:
            if m["sample"] == tumor:
                map.append(m)
            if m["sample"] == normal:
                map.append(m)
                if normal not in used_normals:
                    used_normals.add(normal)
        return map

    def get_mapping_for_unpaired_tumor(self, tumor, mapping):
        map = []
        for m in mapping:
            if m["sample"] == tumor:
                map.append(m)
        return map

    def write_to_file(self, fname, s):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = os.path.join(self.OUTPUT_DIR, fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)

    def write_historical_pairing_file(self, pairing_file_str):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = PAIRING_FILE_LOCATION
        with open(output, "w+") as fh:
            fh.write(pairing_file_str)
        os.chmod(output, 0o777)

    def create_unpaired_txt_file(self):
        # Add runDate
        # TODO: Check is this needed
        fields = [
            settings.CMO_SAMPLE_TAG_METADATA_KEY,
            settings.PATIENT_ID_METADATA_KEY,
            settings.SAMPLE_ID_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            "runMode",
            settings.CMO_SAMPLE_CLASS_METADATA_KEY,
            "baitSet",
            "runDate",
        ]
        unpaired_string = "\t".join(fields) + "\tPossible Reason?"
        for patient_id in self.patients:
            patient = self.patients[patient_id]
            unpaired_string += patient.create_unpaired_string(fields)
        return self.write_to_file("sample_unpaired.txt", unpaired_string)

    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_notifier_id, msg)
        e = event.to_dict()
        send_notification.delay(e)

    def get_recipes(self):
        recipe = [
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
            mapping.extend(patient.create_mapping_json())
            if patient.unpaired_samples:
                mapping.extend(patient.create_unpaired_mapping_json())
        self.write_to_file("sample_mapping_json.json", json.dumps(mapping))
        return mapping

    def create_conflict_samples_txt_file(self):
        """
        TODO: Check is this needed
        :return:
        """
        fields = [
            settings.CMO_SAMPLE_TAG_METADATA_KEY,
            settings.PATIENT_ID_METADATA_KEY,
            settings.SAMPLE_ID_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            "runMode",
            settings.CMO_SAMPLE_CLASS_METADATA_KEY,
            "baitSet",
            "runDate",
        ]
        conflict_string = "\t".join(fields) + "\t" + "Conflict Reason"
        for patient_id in self.patients:
            patient = self.patients[patient_id]
            conflict_string += patient.create_conflict_string(fields)
        return self.write_to_file("sample_conflict.txt", conflict_string)

    def create_pairing_input(self):
        pairing_json = []
        for patient_id in self.patients:
            pairing_json.extend(self.patients[patient_id].create_pairing_json())
        # self.write_historical_pairing_file(json.dumps(pairing_json))
        self.write_to_file("sample_pairing_json.json", json.dumps(pairing_json))
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

    def _validate_to_str(self, data):
        """
        Make sure data can be outputed as a string
        """
        if isinstance(data, str):
            return data
        else:
            new_str = unicodedata.normalize("NFKD", data)
            return new_str
        return ""

    def create_tracker_file(self):
        """
        Creates the string for tracker

        String is tab-delimited; special consideration taken so that the first two columns
        is the Tumor/Normal pairing (if the row Sample is a tumor) or
        Normal/"N/A" (if row sample is a normal)

        The rest of the columns follow the metadata field names in the order set in lists key_order and extra_keys

        key_order has specifically formatted header values, as defined by the PMs, so they needed to be separate;
        extra_keys values are the metadata field names in the database, used as headers
        """
        tracker = ""
        key_order = ["investigatorSampleId", "sampleName", "sampleClass"]
        key_order += ["baitSet", settings.REQUEST_ID_METADATA_KEY]
        extra_keys = [
            "tumorOrNormal",
            "species",
            settings.RECIPE_METADATA_KEY,
            settings.SAMPLE_CLASS_METADATA_KEY,
            settings.SAMPLE_ID_METADATA_KEY,
            settings.PATIENT_ID_METADATA_KEY,
        ]
        extra_keys += [
            "investigatorName",
            "investigatorEmail",
            "piEmail",
            "labHeadName",
            "labHeadEmail",
            "preservation",
        ]
        extra_keys += ["dataAnalystName", "dataAnalystEmail", "projectManagerName", "investigatorId", "cmoSampleName"]

        tracker = "CMO_Sample_ID\tCollaborator_ID_(or_DMP_Sample_ID)\tHistorical_Investigator_ID_(for_CCS_use)\tSample_Class_(T/N)\tBait_set_(Agilent/_IDT/WGS)\tIGO_Request_ID_(Project_ID)\t"
        for key in extra_keys:
            tracker += key + "\t"
        tracker = tracker.strip() + "\n"

        seen = set()

        for patient_id in self.patients:
            patient = self.patients[patient_id]
            for sample_id in patient.all_samples:  # must do this to account for unpaired normals
                sample = patient.all_samples[sample_id]
                meta = sample.dedupe_metadata_values()
                if sample.cmo_sample_name not in seen:
                    seen.add(sample.cmo_sample_name)
                    if not sample.conflict:  # metadata is valid sample
                        running = list()
                        running.append(sample.cmo_sample_name)
                        for key in key_order:
                            v = meta[key]
                            s = self._validate_to_str(v)
                            running.append(s)
                        for key in extra_keys:
                            s = self._validate_to_str(meta[key])
                            running.append(s)
                        tracker += "\t".join(running) + "\n"
        return self.write_to_file("sample_tracker.txt", tracker)

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
