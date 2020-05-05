"""
Helix Filters Operator

Constructs input JSON for the Helix Filters pipeline and then
submits them as runs
"""
import os
import logging
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from .construct_helix_filters_input import construct_helix_filters_input
LOGGER = logging.getLogger(__name__)


class HelixFiltersOperator(Operator):
    """
    Constructs input JSON for the Helix Filters pipeline and then
    submits them as runs
    """
    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        APIRunCreateSerializer
        """
        run_ids = self.run_ids
        input_json = construct_helix_filters_input(run_ids)
        number_of_runs = len(run_ids)
        name = "HELIX FILTERS OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json['project_prefix']
        input_json = add_output_file_names(input_json, pipeline_version)

        helix_filters_outputs_job_data = {
            'app': app,
            'inputs': input_json,
            'name': name,
            'tags': tags}

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both
        """
        output_directory = None
        if project_prefix:
            tags["project_prefix"] = project_prefix 
            if self.job_group_id:
                output_directory = os.path.join(pipeline.output_directory,
                                                "roslin",
                                                project_prefix,
                                                pipeline_version,
                                                self.job_group_id)

            helix_filters_outputs_job_data['output_directory'] = output_directory

        helix_filters_outputs_job = [(APIRunCreateSerializer(
            data=helix_filters_outputs_job_data), input_json)]

        return helix_filters_outputs_job


    def add_output_file_names(self, json_data, pipeline_version):
        """
        Adds strings that's used by the CWL for output file names
        """
        project_prefix = json_data["project_prefix"]
        json_data["roslin_version_string"] = pipeline_version
        json_data["analyst_file"] = "%s.muts.maf" % project_prefix
        json_data["analysis_gene_cna_file"] = "%s.gene.cna.txt" % project_prefix
        json_data["portal_file"] = "data_mutations_extended.txt"
        json_data["portal_CNA_file"] = "data_CNA.txt"

        return json_data
