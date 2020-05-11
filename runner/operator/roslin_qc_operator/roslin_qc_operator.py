"""
RoslinQcOperator

Constructs input JSON for the roslin QC pipeline and then
submits them as runs
"""
import os
import logging
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from .construct_roslin_qc_outputs import construct_roslin_qc_input
LOGGER = logging.getLogger(__name__)


class RoslinQcOperator(Operator):
    """
    Constructs input JSON for the roslin QC pipeline and then
    submits them as runs
    """
    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        APIRunCreateSerializer
        """
        run_ids = self.run_ids
        input_json = construct_roslin_qc_input(run_ids)
        number_of_runs = len(run_ids)
        name = "ROSLIN QC OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json['project_prefix']

        tags = {"tumor_sample_names": input_json['tumor_sample_names'],
                "normal_sample_names": input_json['normal_sample_names']}

        roslin_qc_outputs_job_data = {
            'app': app,
            'inputs': input_json,
            'name': name,
            'notify_for_outputs': ['qc_pdf'],
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

            roslin_qc_outputs_job_data['output_directory'] = output_directory

        roslin_qc_outputs_job = [(APIRunCreateSerializer(
            data=roslin_qc_outputs_job_data), input_json)]

        return roslin_qc_outputs_job
