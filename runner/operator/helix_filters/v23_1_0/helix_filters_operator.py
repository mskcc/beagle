"""
Helix Filters Operator

Constructs input JSON for the Helix Filters pipeline and then
submits them as runs
"""
import os
import logging
from notifier.models import JobGroup
from runner.models import Pipeline, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .construct_helix_filters_input import construct_helix_filters_input, get_project_prefix

LOGGER = logging.getLogger(__name__)


class HelixFiltersOperator(Operator):
    """
    Constructs input JSON for the Helix Filters pipeline and then
    submits them as runs
    """

    ARGOS_NAME = "argos"
    ARGOS_VERSION = "1.7.0"

    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        RunCreator
        """
        argos_run_ids = self.run_ids
        input_json = construct_helix_filters_input(argos_run_ids)
        number_of_runs = len(argos_run_ids)
        name = "HELIX FILTERS OUTPUTS %s runs [%s,..] " % (number_of_runs, argos_run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json["project_prefix"]
        lab_head_email = input_json["lab_head_email"]
        input_json["helix_filter_version"] = pipeline_version
        input_json = self.add_output_file_names(input_json, pipeline_version)
        tags = {"project_prefix": project_prefix, "argos_run_ids": argos_run_ids, "labHeadEmail": lab_head_email}
        log_directory = self.get_log_directory()
        helix_filters_outputs_job_data = {
            "app": app,
            "inputs": input_json,
            "name": name,
            "tags": tags,
            "log_directory": log_directory,
        }

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both

        Going by argos pipeline version id, assuming all runs use the same argos version
        """
        argos_run = Run.objects.get(id=argos_run_ids[0])
        argos_pipeline = argos_run.app

        output_directory = None
        if project_prefix:
            tags["project_prefix"] = project_prefix
            if self.job_group_id:
                jg = JobGroup.objects.get(id=self.job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(
                    pipeline.output_directory, self.ARGOS_NAME, project_prefix, self.ARGOS_VERSION, jg_created_date
                )
            helix_filters_outputs_job_data["output_directory"] = output_directory
        helix_filters_outputs_job = [RunCreator(**helix_filters_outputs_job_data)]
        return helix_filters_outputs_job

    def add_output_file_names(self, json_data, pipeline_version):
        """
        Adds strings that's used by the CWL for output file names
        """
        project_prefix = json_data["project_prefix"]
        json_data["argos_version_string"] = pipeline_version
        json_data["analysis_mutations_filename"] = project_prefix + ".muts.maf"
        json_data["analysis_gene_cna_filename"] = project_prefix + ".gene.cna.txt"
        json_data["analysis_sv_filename"] = project_prefix + ".svs.maf"
        json_data["analysis_segment_cna_filename"] = project_prefix + ".seg.cna.txt"
        json_data["cbio_segment_data_filename"] = project_prefix + "_data_cna_hg19.seg"
        json_data["cbio_meta_cna_segments_filename"] = project_prefix + "_meta_cna_hg19_seg.txt"
        json_data["analysis_mutations_share_filename"] = project_prefix + ".muts.share.maf"
        return json_data

    def get_log_directory(self):
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        log_directory_prefix = get_project_prefix(self.run_ids)
        log_directory = os.path.join(
            pipeline.log_directory,
            self.ARGOS_NAME,
            log_directory_prefix,
            self.ARGOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return log_directory
