import os

from django.conf import settings
from django.db.models import Q
from utils.sample_utils import get_samples_igo, pair_samples_igo

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


class ArgosOperator(Operator):
    ARGOS_NAME = "argos"
    ARGOS_VERSION = "1.8.0"

    def get_jobs(self):
        argos_jobs = list()

        files, cnt_tumors = self.get_files(self.request_id)

        if cnt_tumors == 0:
            cant_do = CantDoEvent(self.job_group_notifier_id).to_dict()
            send_notification.delay(cant_do)
            all_normals_event = SetLabelEvent(self.job_group_notifier_id, "all_normals").to_dict()
            send_notification.delay(all_normals_event)
            return argos_jobs

        pipeline = self.get_pipeline_id()
        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            pass

        samples_igo = self.get_tumor_igo_samples_from_files(files)
        return None

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

    def get_tumor_igo_samples_from_files(self, files):
        """
        Returns only tumor IGO samples
        """
        patient_ids = dict()
        samples_igo = list()

        for f in files:
            metadata = f.metadata
            patient_id = metadata[settings.PATIENT_ID_METADATA_KEY]
            ci_tag = metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
            sample_type = metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY]
            if "normal" not in (sample_type.lower() or ""):
                patient_ids.setdefault(patient_id, set()).add(ci_tag)

        for patient_id in patient_ids:
            samples_igo.append(get_samples_igo(patient_id, self.request_id, files))

        return samples_igo

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
            self.get_project_prefix(),
            self.ARGOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return log_directory

    def links_to_files(self):
        jira_id = JobGroupNotifier.objects.get(id=self.job_group_notifier_id).jira_id
        result = dict()
        result["Sample Pairing"] = (
            f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_pairing.txt"
        )
        result["Sample Mapping"] = (
            f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_mapping.txt"
        )
        result["Sample Data Clinical"] = (
            f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{jira_id}/preview/sample_data_clinical.txt"
        )
        return result

    def get_project_prefix(self):
        project_prefix = set()
        tumors = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: self.request_id, "tumorOrNormal": "Tumor"},
            filter_redact=True,
            values_metadata=settings.REQUEST_ID_METADATA_KEY,
        )
        for tumor in tumors:
            project_prefix.add(tumor)
        return "_".join(sorted(project_prefix))
