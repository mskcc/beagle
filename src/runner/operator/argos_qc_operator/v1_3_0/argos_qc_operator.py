"""
ArgosQcOperator

Constructs input JSON for the argos QC pipeline and then
submits them as runs
"""

import os
import logging
from notifier.models import JobGroup
from runner.models import Pipeline, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .construct_argos_qc_outputs import construct_argos_qc_input, get_output_directory_prefix, get_project_prefix

LOGGER = logging.getLogger(__name__)


class ArgosQcOperator(Operator):
    """
    Constructs input JSON for the argos QC pipeline and then
    submits them as runs
    """

    ARGOS_NAME = "argos"
    ARGOS_VERSION = "1.8.0"

    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        RunCreator
        """
        run_ids = self.run_ids
        input_json = construct_argos_qc_input(run_ids)
        number_of_runs = len(run_ids)
        name = "ARGOS QC OUTPUTS %s runs [%s,..] " % (number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json["project_prefix"]
        output_directory_prefix = get_output_directory_prefix(self.run_ids)
        log_directory = self.get_log_directory()
        tags = {
            "tumor_sample_names": input_json["tumor_sample_names"],
            "normal_sample_names": input_json["normal_sample_names"],
        }

        argos_qc_outputs_job_data = {
            "app": app,
            "inputs": input_json,
            "name": name,
            "notify_for_outputs": ["qc_pdf"],
            "tags": tags,
            "log_directory": log_directory,
        }

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both

        Also use argos version number for output instead of pipeline version
        that's listed in Beagle
        """
        argos_run = Run.objects.get(id=run_ids[0])
        argos_pipeline = argos_run.app

        output_directory = None
        if self.output_directory_prefix:
            project_prefix = self.output_directory_prefix

        if project_prefix:
            tags["project_prefix"] = project_prefix
            output_prefix = output_directory_prefix if output_directory_prefix else project_prefix
            if self.job_group_id:
                jg = JobGroup.objects.get(id=self.job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(
                    pipeline.output_directory, "argos", output_prefix, argos_pipeline.version, jg_created_date
                )
            argos_qc_outputs_job_data["output_directory"] = output_directory
        argos_qc_outputs_job = [RunCreator(**argos_qc_outputs_job_data)]
        return argos_qc_outputs_job

    def get_log_directory(self):
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory_prefix = get_project_prefix(self.run_ids)
        output_directory = os.path.join(
            pipeline.log_directory,
            self.ARGOS_NAME,
            output_directory_prefix,
            self.ARGOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return output_directory
