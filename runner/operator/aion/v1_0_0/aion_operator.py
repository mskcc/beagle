"""
Aion Operator

Constructs input JSON for the Aion pipeline and then
submits them as runs
"""
import os
import datetime
import logging
from study.objects import StudyObject
from runner.models import Run, Pipeline
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
            project_prefixes = study_obj.proj_prefixes
            samples = study_obj.samples
            # How should we separate dmp samples from regular samples in the study obj?

            dmp_samples = []

            number_of_runs = len(run_ids)
            name = "AION merging %i runs for lab head email %s" % (number_of_runs, study_obj.lab_head_email)

            app = self.get_pipeline_id()
            input_json = self.build_input_json(run_ids, project_prefixes, study_id, dmp_samples)
            tags = {"study_id": study_id, "num_runs_merged": len(run_ids)}
            print(input_json)

            aion_outputs_job_data = {"app": app, "inputs": input_json, "name": name, "tags": tags}

            aion_outputs_jobs.append(RunCreator(**aion_outputs_job_data))
        return aion_outputs_jobs

    def build_input_json(self, run_ids, project_prefixes, study_id, dmp_samples):
        #    run_ids = self.run_ids
        merge_date = datetime.datetime.now().strftime("%Y_%m_%d")
        directories = set()
        input_json = dict()

        input_json["project_description"] = "[%s] Includes samples received at IGO for Project ID(s): %s" % (
            merge_date,
            ", ".join(sorted(project_prefixes)),
        )
        input_json["study_id"] = study_id
        input_json["project_title"] = "CMO Merged Study for Principal Investigator (%s)" % study_id

        for run_id in run_ids:
            run = Run.objects.get(id=run_id)
            if 'helix_filters' in run.app.name:
                run_portal_dir = os.path.join(run.output_directory, "portal")
                if os.path.isdir(run_portal_dir):
                    directories.add(run_portal_dir)
            if 'ultron' in run.app.name:
                output_dir = run.output_directory
                if os.path.isdir(output_dir):
                    directories.add(output_dir)
        input_json["directories"] = list()
        input_json["sample_data_clinical_files"] = [self.create_data_clinical_file(run_ids, dmp_samples)]
        for portal_directory in directories:
            input_json["directories"].append({"class": "Directory", "path": portal_directory})
        return input_json

    def create_data_clinical_file(self, run_id_list, dmp_samples):
        files = list()
        pipeline_names = set()
        pipeline_githubs = set()
        pipeline_versions = set()
        for run_id in run_id_list:
            argos_run = Run.objects.get(id=run_id)
            pipeline = argos_run.app
            pipeline_names.add(pipeline.name)
            pipeline_githubs.add(pipeline.github)
            pipeline_versions.add(pipeline.version)
            files = files + get_files_from_run(argos_run)
        data_clinical_content = generate_sample_data_content(
            files,
            pipeline_name=",".join(pipeline_names),
            pipeline_github=",".join(pipeline_githubs),
            pipeline_version=",".join(pipeline_versions),
            dmp_samples=dmp_samples,
        )
        data_clinical_content = data_clinical_content.strip()
        return {"class": "File", "basename": "sample_data_clinical.txt", "contents": data_clinical_content}

    def get_lab_head(self, argos_run_ids):
        lab_head_emails = set()
        for argos_run_id in argos_run_ids:
            argos_run = Run.objects.get(id=argos_run_id)
            lab_head_email = argos_run.tags["labHeadEmail"]
            if lab_head_email:
                lab_head_emails.add(lab_head_email)
        if len(lab_head_emails) > 1:
            #         LOGGER.warn("Multiple lab head emails found; merge output directory unclear.")
            print("Multiple lab head emails found; merge output directory unclear.")
        # TODO: get clarity on where to output if there are multiple pi found
        if lab_head_emails:
            return sorted(lab_head_emails)[0]
        return None

    def get_helix_filter_run_ids(self, lab_head_email):
        runs = Run.objects.filter(status=4, app__name="argos_helix_filters")
        helix_filter_runs = set()
        for i in runs:
            argos_run_ids = i.tags["run_ids"]
            for run_id in argos_run_ids:
                run = Run.objects.get(id=run_id)
                try:
                    curr_lab_head_email = run.tags["labHeadEmail"]
                    if lab_head_email.lower() in curr_lab_head_email.lower():
                        helix_filter_runs.add(i.id)
                except KeyError:
                    print("labHeadEmail not in this run %s", run_id)
        return sorted(helix_filter_runs)
