import uuid

from django.conf import settings
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .construct_argos_pair import construct_argos_jobs
from runner.models import Pipeline
from .bin.make_sample import build_sample
from notifier.events import UploadAttachmentEvent, OperatorRequestEvent, CantDoEvent, SetLabelEvent
from notifier.tasks import send_notification
from notifier.helper import generate_sample_data_content
from runner.run.processors.file_processor import FileProcessor
from file_system.repository.file_repository import FileRepository
from .bin.retrieve_samples_by_query import build_dmp_sample, get_pooled_normal_files, build_pooled_normal_sample_by_file
from .bin.make_sample import format_sample_name


class ArgosOperator(Operator):
    def get_jobs(self):

        argos_jobs = list()

        if self.request_id:
            files = FileRepository.filter(
                queryset=self.files,
                metadata={settings.REQUEST_ID_METADATA_KEY: self.request_id, settings.IGO_COMPLETE_METADATA_KEY: True},
                filter_redact=True,
            )

            cnt_tumors = FileRepository.filter(
                queryset=self.files,
                metadata={
                    settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    "tumorOrNormal": "Tumor",
                    settings.IGO_COMPLETE_METADATA_KEY: True,
                },
                filter_redact=True,
            ).count()
        elif self.pairing:
            files, cnt_tumors = self.get_files_for_pairs()

        if cnt_tumors == 0:
            cant_do = CantDoEvent(self.job_group_notifier_id).to_dict()
            send_notification.delay(cant_do)
            all_normals_event = SetLabelEvent(self.job_group_notifier_id, "all_normals").to_dict()
            send_notification.delay(all_normals_event)
            return argos_jobs

        data = list()
        for f in files:
            sample = dict()
            sample["id"] = f.file.id
            sample["path"] = f.file.path
            sample["file_name"] = f.file.file_name
            sample["metadata"] = f.metadata
            data.append(sample)

        files = list()
        samples = list()
        # group by igoId
        igo_id_group = dict()
        for sample in data:
            igo_id = sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            sample = igo_id_group[igo_id][0]
            sample_name = sample["metadata"][settings.CMO_SAMPLE_NAME_METADATA_KEY]
            if "poolednormal" in sample_name.lower():
                samples.append(build_sample(igo_id_group[igo_id], ignore_sample_formatting=True))
            else:
                samples.append(build_sample(igo_id_group[igo_id]))

        argos_inputs, error_samples = construct_argos_jobs(samples, self.pairing)
        number_of_inputs = len(argos_inputs)

        sample_pairing = ""
        sample_mapping = ""
        pipeline = self.get_pipeline_id()

        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            pass

        check_for_duplicates = list()
        for i, job in enumerate(argos_inputs):
            tumor_sample_name = job["pair"][0]["ID"]
            for p in job["pair"][0]["R1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][0]["R2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][0]["zR1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][0]["zR2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][0]["bam"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)

            normal_sample_name = job["pair"][1]["ID"]
            for p in job["pair"][1]["R1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][1]["R2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][1]["zR1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][1]["zR2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)
            for p in job["pair"][1]["bam"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in files:
                    files.append(filepath)

            name = "ARGOS %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            assay = job["assay"]
            pi = job["pi"]
            pi_email = job["pi_email"]

            sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"

            tags = {
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                "sampleNameTumor": tumor_sample_name,
                "sampleNameNormal": normal_sample_name,
                "labHeadName": pi,
                "labHeadEmail": pi_email,
            }
            if self.output_directory_prefix:
                tags["output_directory_prefix"] = self.output_directory_prefix
            argos_jobs.append(RunCreator(app=pipeline, inputs=job, name=name, tags=tags))

        operator_run_summary = UploadAttachmentEvent(
            self.job_group_notifier_id, "sample_pairing.txt", sample_pairing
        ).to_dict()
        send_notification.delay(operator_run_summary)

        mapping_file_event = UploadAttachmentEvent(
            self.job_group_notifier_id, "sample_mapping.txt", sample_mapping
        ).to_dict()
        send_notification.delay(mapping_file_event)

        data_clinical = generate_sample_data_content(
            files,
            pipeline_name=pipeline_obj.name,
            pipeline_github=pipeline_obj.github,
            pipeline_version=pipeline_obj.version,
        )
        sample_data_clinical_event = UploadAttachmentEvent(
            self.job_group_notifier_id, "sample_data_clinical.txt", data_clinical
        ).to_dict()
        send_notification.delay(sample_data_clinical_event)

        self.evaluate_sample_errors(error_samples)
        self.summarize_pairing_info(argos_inputs)

        return argos_jobs

    def get_files_for_pairs(self):
        all_files = []
        cnt_tumors = 0
        for pair in self.pairing.get("pairs"):
            tumor_sample = pair["tumor"]
            normal_sample = pair["normal"]
            tumors = self.get_regular_sample(tumor_sample, "Tumor")
            current_cnt_tumors = len(tumors)
            cnt_tumors += current_cnt_tumors
            normals = self.get_regular_sample(normal_sample, "Normal")
            if not normals and current_cnt_tumors > 0:  # get from pooled normal
                bait_set = tumors[0].metadata["baitSet"]
                run_ids = list()
                for tumor in tumors:
                    run_id = tumor.metadata["runId"]
                    if run_id:
                        run_ids.append(run_id)
                run_ids.sort()
                preservation_types = tumors[0].metadata["preservation"]
                normal_sample_id = normal_sample["sample_id"]
                normals = list()
                pooled_normal_files, bait_set_reformatted, sample_name = get_pooled_normal_files(
                    run_ids, preservation_types, bait_set
                )
                for f in pooled_normal_files:
                    metadata = build_pooled_normal_sample_by_file(
                        f, run_ids, preservation_types, bait_set_reformatted, sample_name
                    )["metadata"]
                    sample = f
                    sample.metadata = metadata
                    normals.append(sample)
            for file in list(tumors):
                if file not in all_files:
                    all_files.append(file)
            for file in list(normals):
                if file not in all_files:
                    all_files.append(file)
        return all_files, cnt_tumors

    def get_regular_sample(self, sample_data, tumor_type):
        sample_id = sample_data["sample_id"]
        sample = FileRepository.filter(
            queryset=self.files,
            metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample_id, settings.IGO_COMPLETE_METADATA_KEY: True},
            filter_redact=True,
        )
        if not sample:  # try dmp sample
            if "patient_id" in sample_data:
                patient_id = sample_data["patient_id"]
            if "bait_set" in sample_data:
                bait_set = sample_data["bait_set"]
            dmp_bam_id = sample_id.replace("s_", "").replace("_", "-")
            data = FileRepository.filter(queryset=self.files, metadata={"external_id": dmp_bam_id})
            sample = list()
            for i in data:
                s = i
                metadata = build_dmp_sample(i, patient_id, bait_set, tumor_type)["metadata"]
                s.metadata = metadata
                sample.append(i)
        return sample

    def summarize_pairing_info(self, argos_inputs):
        num_pairs = len(argos_inputs)
        num_dmp_normals = 0
        num_pooled_normals = 0
        num_outside_req = 0
        num_within_req = 0
        other_requests_matched = list()
        for i, job in enumerate(argos_inputs):
            tumor = job["pair"][0]
            normal = job["pair"][1]
            req_t = tumor["request_id"]
            req_n = normal["request_id"]
            specimen_type_n = normal["specimen_type"]
            if specimen_type_n.lower() in "DMP Normal".lower():
                num_dmp_normals += 1
            elif specimen_type_n.lower() in "Pooled Normal".lower():
                num_pooled_normals += 1
            elif req_t.strip() != req_n.strip():
                num_outside_req += 1
                data = dict()
                data["sample_name"] = tumor["ID"]
                data["matched_sample_name"] = normal["ID"]
                data["normal_request"] = req_n
                other_requests_matched.append(data)
            else:
                num_within_req += 1
        s = "Number of pairs: %i\n\n" % num_pairs
        s += "%i samples matched with DMP Normal\n" % num_dmp_normals
        s += "%i samples matched with pooled normals\n" % num_pooled_normals
        s += "%i samples matched with normal from different request" % num_outside_req

        if num_outside_req > 0:
            s += "\n\nMatched samples fom different request\n"
            s += "| Sample Name | Matched Normal | Request Normal |\n"
            for i in other_requests_matched:
                sample_name = i["sample_name"]
                matched_sample = i["matched_sample_name"]
                normal_request = i["normal_request"]
                s += "| %s | %s | %s |\n" % (sample_name, matched_sample, normal_request)

        self.send_message(s)

    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_notifier_id, msg)
        e = event.to_dict()
        send_notification.delay(e)

    def evaluate_sample_errors(self, error_samples):
        s = list()
        unformatted_s = list()
        unformatted_s.append("IGO Sample ID\tSample Name / Error\tPatient ID\tSpecimen Type\n")
        for sample in error_samples:
            sample_name = sample.get("SM", "missingSampleName")
            sample_id = sample.get("sample_id", "missingSampleId")
            patient_id = sample.get("patient_id", "missingPatientId")
            specimen_type = sample.get("specimen_type", "missingSpecimenType")
            s.append("| " + sample_id + " | " + sample_name + " |" + patient_id + " |" + specimen_type + " |")
            unformatted_s.append(sample_id + "\t" + sample_name + "\t" + patient_id + "\t" + specimen_type + "\n")

        msg = """
        Number of samples with error: {number_of_errors}

        Error samples (also see error_sample_formatting.txt):
        | IGO Sample ID | Sample Name / Error | Patient ID | Specimen Type |
        {error_sample_names}
        """

        msg = msg.format(number_of_errors=str(len(error_samples)), error_sample_names="\n".join(s))

        self.send_message(msg)

        sample_errors_event = UploadAttachmentEvent(
            self.job_group_notifier_id, "error_sample_formatting.txt", "".join(unformatted_s)
        ).to_dict()
        send_notification.delay(sample_errors_event)

    def format_sample_name(self, *args, **kwargs):
        return format_sample_name(*args, **kwargs)

    def on_job_fail(self, run):
        cmo_sample_name = run.tags.get("sampleNameTumor")
        files = FileRepository.filter(queryset=self.files, metadata={"cmoSampleName": cmo_sample_name})
        if files:
            qc_report = files[0].metadata["qcReports"]
            sample_id = files[0].metadata["sampleId"]
            """
            {
                "comments": "Suboptimal quantity",
                "qcReportType": "LIBRARY",
                "IGORecommendation": "Try",
                "investigatorDecision": "Continue processing"
            }
            """
            report_str = ""
            for report in qc_report:
                report_str += "{comments}\t{qc_report_type}\t{igo_recommendation}\t{investigator_decision}\n".format(
                    comments=report["comments"],
                    qc_report_type=report["qcReportType"],
                    igo_recommendation=report["IGORecommendation"],
                    investigator_decision=report["investigatorDecision"],
                )
            msg = """
cmoSampleId: {cmo_sample_name}
sampleId: {sample_id}
Comments\tQC Report Type\tIGORecommendation\tInvestigator Decision\n
{report_str}
""".format(
                cmo_sample_name=cmo_sample_name, sample_id=sample_id, report_str=report_str
            )

            file_name = "{cmo_sample_name}_igo_qc_report".format(cmo_sample_name=cmo_sample_name)
            sample_errors_event = UploadAttachmentEvent(self.job_group_notifier_id, file_name, msg).to_dict()
            send_notification.delay(sample_errors_event)
