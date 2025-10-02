import os

from django.conf import settings
from django.db.models import Q

from file_system.models import FileGroup
from file_system.repository.file_repository import FileRepository
from notifier.events import (
    CantDoEvent,
    LocalStoreAttachmentsEvent,
    OperatorRequestEvent,
    SetLabelEvent,
    UploadAttachmentEvent,
)
from notifier.helper import generate_sample_data_content
from notifier.models import JobGroup, JobGroupNotifier
from notifier.tasks import send_notification
from runner.models import Pipeline
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from runner.run.processors.file_processor import FileProcessor

from .bin.make_sample import build_sample, format_sample_name
from .bin.retrieve_samples_by_query import build_dmp_sample, build_pooled_normal_sample_by_file, get_pooled_normal_files
from .construct_argos_pair import construct_argos_jobs, get_project_prefix


class ArgosOperator(Operator):
    ARGOS_NAME = "argos"
    ARGOS_VERSION = "1.7.0"

    def get_jobs(self):

        argos_jobs = list()
        dmp_samples = list()
        if self.pairing:
            files, cnt_tumors, dmp_samples = self.get_files_for_pairs(self.pairing)
        elif self.request_id:
            files, cnt_tumors = self.get_files(self.request_id)

        if cnt_tumors == 0:
            cant_do = CantDoEvent(self.job_group_notifier_id).to_dict()
            send_notification.delay(cant_do)
            all_normals_event = SetLabelEvent(self.job_group_notifier_id, "all_normals").to_dict()
            send_notification.delay(all_normals_event)
            return argos_jobs

        data = self.build_data_list(files)

        samples = self.get_samples_from_data(data)
        argos_inputs, error_samples = construct_argos_jobs(samples, self.pairing, logger=self.logger)
        sample_pairing = self.get_pairing_from_argos_inputs(argos_inputs)
        sample_mapping, filepaths = self.get_mapping_from_argos_inputs(argos_inputs)
        argos_jobs = self.get_argos_jobs(argos_inputs)
        pipeline = self.get_pipeline_id()

        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            pass

        operator_run_summary_local = LocalStoreAttachmentsEvent(
            self.job_group_notifier_id, "sample_pairing.txt", sample_pairing
        ).to_dict()
        send_notification.delay(operator_run_summary_local)
        mapping_file_event_local = LocalStoreAttachmentsEvent(
            self.job_group_notifier_id, "sample_mapping.txt", sample_mapping
        ).to_dict()
        send_notification.delay(mapping_file_event_local)
        data_clinical = generate_sample_data_content(
            filepaths,
            pipeline_name=pipeline_obj.name,
            pipeline_github=pipeline_obj.github,
            pipeline_version=pipeline_obj.version,
            dmp_samples=dmp_samples,
        )
        sample_data_clinical_local = LocalStoreAttachmentsEvent(
            self.job_group_notifier_id, "sample_data_clinical.txt", data_clinical
        ).to_dict()
        send_notification.delay(sample_data_clinical_local)
        self.evaluate_sample_errors(error_samples)
        self.summarize_pairing_info(argos_inputs)

        return argos_jobs

    def get_argos_jobs(self, argos_inputs):
        argos_jobs = list()
        number_of_inputs = len(argos_inputs)
        for i, job in enumerate(argos_inputs):
            tumor_sample_name = job["tumor"]["ID"]
            normal_sample_name = job["normal"]["ID"]

            name = "ARGOS %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            assay = job["assay"]
            pi = job["pi"]
            pi_email = job["pi_email"]

            tags = {
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                "sampleNameTumor": tumor_sample_name,
                "sampleNameNormal": normal_sample_name,
                "labHeadName": pi,
                "labHeadEmail": pi_email,
            }
            pipeline = self.get_pipeline_id()
            log_prefix = f"{tumor_sample_name}_{normal_sample_name}"
            log_directory = self.get_log_directory()
            if self.output_directory_prefix:
                tags["output_directory_prefix"] = self.output_directory_prefix
            argos_jobs.append(
                RunCreator(
                    app=pipeline, inputs=job, name=name, tags=tags, log_prefix=log_prefix, log_directory=log_directory
                )
            )
        return argos_jobs

    def get_mapping_from_argos_inputs(self, argos_inputs):
        sample_mapping = ""
        check_for_duplicates = list()
        filepaths = list()
        for i, job in enumerate(argos_inputs):
            tumor_sample_name = job["tumor"]["ID"]
            for p in job["tumor"]["R1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["tumor"]["R2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["tumor"]["zR1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["tumor"]["zR2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["tumor"]["bam"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([tumor_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)

            normal_sample_name = job["normal"]["ID"]
            for p in job["normal"]["R1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["normal"]["R2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["normal"]["zR1"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["normal"]["zR2"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
            for p in job["normal"]["bam"]:
                filepath = FileProcessor.parse_path_from_uri(p["location"])
                file_str = "\t".join([normal_sample_name, filepath]) + "\n"
                if file_str not in check_for_duplicates:
                    check_for_duplicates.append(file_str)
                    sample_mapping += file_str
                if filepath not in filepaths:
                    filepaths.append(filepath)
        return sample_mapping, filepaths

    def get_pairing_from_argos_inputs(self, argos_inputs):
        sample_pairing = ""
        for i, job in enumerate(argos_inputs):
            tumor_sample_name = job["tumor"]["ID"]
            normal_sample_name = job["normal"]["ID"]
            sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"
        return sample_pairing

    def get_samples_from_data(self, data):
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
        return samples

    def get_files_for_pairs(self, pairing):
        all_files = []
        cnt_tumors = 0
        dmp_samples = list()
        for pair in pairing.get("pairs"):
            tumor_sample = pair["tumor"]
            normal_sample = pair["normal"]
            tumor, is_dmp_tumor_sample = self.get_regular_sample(tumor_sample, "Tumor")
            cnt_tumors += 1
            normal, is_dmp_normal_sample = self.get_regular_sample(normal_sample, "Normal")
            if not normal and tumor:  # get from pooled normal
                normal = list()
                run_ids = list()
                for t_files in tumor:
                    run_id = t_files.metadata["runId"]
                    if run_id:
                        run_ids.append(run_id)
                run_ids.sort()
                tumor_current = tumor.first()
                bait_set = tumor_current.metadata["baitSet"]
                preservation_types = tumor_current.metadata["preservation"]
                sample_origin = tumor_current.metadata["sampleOrigin"]
                pooled_normal_files, bait_set_reformatted, sample_name = get_pooled_normal_files(
                    run_ids, preservation_types, bait_set, sample_origin
                )
                for f in pooled_normal_files:
                    metadata = build_pooled_normal_sample_by_file(
                        f, run_ids, preservation_types, bait_set_reformatted, sample_origin, sample_name
                    )["metadata"]
                    sample = f
                    sample.metadata = metadata
                    normal.append(sample)
            for file in list(tumor):
                if file not in all_files:
                    all_files.append(file)
                if tumor not in dmp_samples:
                    if is_dmp_tumor_sample:
                        dmp_samples.append(tumor)
            for file in list(normal):
                if file not in all_files:
                    all_files.append(file)
                if normal not in dmp_samples:
                    if is_dmp_normal_sample:
                        dmp_samples.append(normal)
        return all_files, cnt_tumors, dmp_samples

    def get_files(self, request_id):
        files = FileRepository.filter(
            queryset=self.files,
            metadata={settings.REQUEST_ID_METADATA_KEY: request_id, settings.IGO_COMPLETE_METADATA_KEY: True},
            filter_redact=True,
        )

        cnt_tumors = FileRepository.filter(
            queryset=self.files,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: request_id,
                "tumorOrNormal": "Tumor",
                settings.IGO_COMPLETE_METADATA_KEY: True,
            },
            filter_redact=True,
        ).count()
        return files, cnt_tumors

    def build_data_list(self, files):
        data = list()
        for f in files:
            sample = dict()
            sample["id"] = f.file.id
            sample["path"] = f.file.path
            sample["file_name"] = f.file.file_name
            sample["metadata"] = f.metadata
            data.append(sample)
        return data

    def get_regular_sample(self, sample_data, tumor_type):
        sample_id = sample_data["sample_id"]
        sample = FileRepository.filter(
            queryset=self.files,
            metadata={settings.CMO_SAMPLE_TAG_METADATA_KEY: sample_id, settings.IGO_COMPLETE_METADATA_KEY: True},
            filter_redact=True,
        )
        is_dmp_sample = False
        request_id = self.request_id
        if not sample:  # try dmp sample
            if "patient_id" in sample_data:
                patient_id = sample_data["patient_id"]
            if "bait_set" in sample_data:
                bait_set = sample_data["bait_set"]
            if "pi" in sample_data:
                pi = sample_data["pi"]
            if "pi_email" in sample_data:
                pi_email = sample_data["pi_email"]
            if "sample_origin" in sample_data:
                sample_origin = sample_data["sample_origin"]
            dmp_bam_id = sample_id.replace("s_", "").replace("_", "-")
            dmp_bam_slug = Q(file__file_group=FileGroup.objects.get(slug="dmp-bams"))
            dmp_bam_files = FileRepository.filter(q=dmp_bam_slug)
            data = FileRepository.filter(queryset=dmp_bam_files, metadata={"external_id": dmp_bam_id})
            sample = list()
            if len(data) > 0:
                s = data[0]
                metadata = build_dmp_sample(
                    s, patient_id, bait_set, tumor_type, request_id, pi, pi_email, sample_origin
                )["metadata"]
                s.metadata = metadata
                if s:
                    is_dmp_sample = True
                    sample.append(s)
        return sample, is_dmp_sample

    def summarize_pairing_info(self, argos_inputs):
        num_pairs = len(argos_inputs)
        num_dmp_normals = 0
        num_pooled_normals = 0
        num_outside_req = 0
        num_within_req = 0
        other_requests_matched = list()
        for i, job in enumerate(argos_inputs):
            tumor = job["tumor"]
            normal = job["normal"]
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
            sample_id = files[0].metadata[settings.SAMPLE_ID_METADATA_KEY]
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

    def get_log_directory(self):
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        log_directory = os.path.join(
            pipeline.log_directory,
            self.ARGOS_NAME,
            get_project_prefix(self.request_id),
            self.ARGOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return log_directory

    def get_dmp_samples_from_argos_inputs(self, argos_inputs):
        dmp_samples = list()
        for i, job in enumerate(argos_inputs):
            pi = job["pi"]
            pi_email = job["pi_email"]
            patient_id = job["patient_id"]
            bait_set = job["assay"]
            tumor_id = job["tumor"]["ID"]
            normal_id = job["normal"]["ID"]
            sample_tumor = dict(pi=pi, bait_set=bait_set, pi_email=pi_email, patient_id=patient_id, sample_id=tumor_id)
            this_sample, is_dmp_sample = self.get_regular_sample(sample_tumor, "Tumor")
            if is_dmp_sample:
                dmp_samples.append(this_sample)
            sample_normal = dict(
                pi=pi, bait_set=bait_set, pi_email=pi_email, patient_id=patient_id, sample_id=normal_id
            )
            this_sample, is_dmp_sample = self.get_regular_sample(sample_normal, "Normal")
            if is_dmp_sample:
                dmp_samples.append(this_sample)
        return dmp_samples

    def links_to_files(self):
        jira_id = JobGroupNotifier.objects.get(id=self.job_group_notifier_id).jira_id
        result = dict()
        result[
            "Sample Pairing"
        ] = f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_pairing.txt"
        result[
            "Sample Mapping"
        ] = f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_mapping.txt"
        result[
            "Sample Data Clinical"
        ] = f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_data_clinical.txt"
        return result
