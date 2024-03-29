"""
Aion Operator

Constructs input JSON for the Aion pipeline and then
submits them as runs
"""
import os
import datetime
import logging
from django.conf import settings
from study.objects import StudyObject
from runner.models import Run, Port
from file_system.models import File
from notifier.helper import generate_sample_data_content
from file_system.repository.file_repository import FileRepository
from runner.run.processors.file_processor import FileProcessor
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator

LOGGER = logging.getLogger(__name__)


class AionOperator(Operator):
    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        RunCreator
        """
        study_objects = StudyObject.get_by_request(self.request_id)
        aion_outputs_jobs = []
        for study_obj in study_objects:
            run_ids = study_obj.run_ids
            study_id = study_obj.study_id
            project_prefixes = study_obj.project_prefixes["Argos"]
            dmp_samples = self._get_dmp_samples(study_obj)

            number_of_runs = len(run_ids)
            name = "AION merging %i runs for study id %s" % (number_of_runs, study_id)

            app = self.get_pipeline_id()
            input_json = self.build_input_json(run_ids, project_prefixes, study_id, dmp_samples)
            tags = {"study_id": study_id, "num_runs_merged": len(run_ids)}

            aion_outputs_job_data = {"app": app, "inputs": input_json, "name": name, "tags": tags}

            aion_outputs_jobs.append(RunCreator(**aion_outputs_job_data))
        return aion_outputs_jobs

    def _get_dmp_samples(self, study_obj):
        samples = study_obj.samples
        sample_files = File.objects.filter(sample__in=samples)
        patient_ids = []
        sample_ids = []
        for single_file in sample_files:
            if single_file.patient_id:
                single_patient_id = single_file.patient_id
                dmp_patient_id = single_patient_id.lstrip("C-")
                if dmp_patient_id not in patient_ids:
                    patient_ids.append(dmp_patient_id)
        DMP_BAMs = FileRepository.filter(
            file_group=settings.DMP_BAM_FILE_GROUP, metadata={"patient__cmo__in": patient_ids}
        )
        for single_bam in DMP_BAMs:
            if single_bam.sample:
                if single_bam.sample not in sample_ids:
                    sample_ids.append(single_bam.sample)
        return sample_ids

    def build_input_json(self, run_ids, project_prefixes, study_id, dmp_samples):
        merge_date = datetime.datetime.now().strftime("%Y_%m_%d")
        directories = set()
        input_json = dict()
        argos_runs = list()

        input_json["project_description"] = "[%s] Includes samples received at IGO for Project ID(s): %s" % (
            merge_date,
            ", ".join(sorted(project_prefixes)),
        )
        input_json["study_id"] = study_id
        input_json["project_title"] = "CMO Merged Study for Principal Investigator (%s)" % study_id

        for app_name in run_ids:
            run_list = run_ids[app_name].values()
            if app_name == "Helix Filters":
                for single_helix_run in run_list:
                    run_portal_dir = os.path.join(single_helix_run.output_directory, "portal")
                    if os.path.isdir(run_portal_dir):
                        directories.add(run_portal_dir)
            if app_name == "Ultron":
                for single_ultron_run in run_list:
                    output_dir = single_ultron_run.output_directory
                    if os.path.isdir(output_dir):
                        directories.add(output_dir)
            if app_name == "Argos":
                argos_runs = run_list

        input_json["directories"] = list()
        input_json["output_directory"] = study_id
        input_json["sample_data_clinical_files"] = [self.create_data_clinical_file(argos_runs, dmp_samples)]
        for portal_directory in directories:
            input_json["directories"].append({"class": "Directory", "path": portal_directory})
        return input_json

    def create_data_clinical_file(self, argos_runs, dmp_samples):
        files = list()
        pipeline_names = set()
        pipeline_githubs = set()
        pipeline_versions = set()
        for argos_run in argos_runs:
            pipeline = argos_run.app
            pipeline_names.add(pipeline.name)
            pipeline_githubs.add(pipeline.github)
            pipeline_versions.add(pipeline.version)
            files = files + self.get_files_from_run(argos_run)
        data_clinical_content = generate_sample_data_content(
            files,
            pipeline_name=",".join(pipeline_names),
            pipeline_github=",".join(pipeline_githubs),
            pipeline_version=",".join(pipeline_versions),
            dmp_samples=dmp_samples,
        )
        data_clinical_content = data_clinical_content.strip()
        return {"class": "File", "basename": "sample_data_clinical.txt", "contents": data_clinical_content}

    def get_files_from_run(self, r):
        files = list()
        inp_port = Port.objects.filter(run_id=r.id, name="pair").first()
        for p in inp_port.db_value[0]["R1"]:
            files.append(FileProcessor.get_file_path(p["location"]))
        for p in inp_port.db_value[0]["R2"]:
            files.append(FileProcessor.get_file_path(p["location"]))
        for p in inp_port.db_value[0]["zR1"]:
            files.append(FileProcessor.get_file_path(p["location"]))
        for p in inp_port.db_value[0]["zR2"]:
            files.append(FileProcessor.get_file_path(p["location"]))
        for p in inp_port.db_value[0]["bam"]:
            files.append(FileProcessor.get_file_path(p["location"]))
        return files
