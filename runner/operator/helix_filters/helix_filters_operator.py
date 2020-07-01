"""
Helix Filters Operator

Constructs input JSON for the Helix Filters pipeline and then
submits them as runs
"""
import os
import logging
from notifier.models import JobGroup
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from file_system.repository.file_repository import FileRepository
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
        argos_run_ids = self.run_ids
        input_json = construct_helix_filters_input(argos_run_ids)
        number_of_runs = len(argos_run_ids)
        name = "HELIX FILTERS OUTPUTS %s runs [%s,..] " % (
            number_of_runs, argos_run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json['project_prefix']
        input_json = self.add_output_file_names(input_json, pipeline_version)
        tags = { "project_prefix": project_prefix, "argos_run_ids": argos_run_ids }

        #TODO:  Remove purity facets seg files from facets_hisens_seg_files
        input_json['facets_hisens_seg_files'] = self.remove_purity_files(input_json['facets_hisens_seg_files'])

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
                jg = JobGroup.objects.get(id=self.job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(pipeline.output_directory,
                                                "argos",
                                                project_prefix,
                                                pipeline_version,
                                                jg_created_date)
            helix_filters_outputs_job_data['output_directory'] = output_directory
        helix_filters_outputs_job = [(APIRunCreateSerializer(
            data=helix_filters_outputs_job_data), input_json)]
        return helix_filters_outputs_job


    def add_output_file_names(self, json_data, pipeline_version):
        """
        Adds strings that's used by the CWL for output file names
        """
        project_prefix = json_data["project_prefix"]
        json_data["argos_version_string"] = pipeline_version
        json_data["analyst_file"] = "%s.muts.maf" % project_prefix
        json_data["analysis_gene_cna_file"] = "%s.gene.cna.txt" % project_prefix
        json_data["portal_file"] = "data_mutations_extended.txt"
        json_data["portal_CNA_file"] = "data_CNA.txt"

        return json_data

    def remove_purity_files(self, data):
        """
        Currently all seg files are in one array output; need to remove the _purity.seg files
        from input_json['facets_hisens_seg_files']
        """
        new_data = list()
        for i in data:
            location = i['location']
            if '_purity.seg' not in location:
                new_data.append(i)
        return new_data

