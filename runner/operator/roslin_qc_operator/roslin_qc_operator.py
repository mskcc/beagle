"""
RoslinQcOperator

Constructs input JSON for the roslin QC pipeline and then
submits them as runs
"""
import logging
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
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
        tags = {"tumor_sample_names": input_json['tumor_sample_names'],
                "normal_sample_names": input_json['normal_sample_names'],
                "project_prefix": input_json['project_prefix'],
                "number_of_runs": number_of_runs}
        roslin_qc_outputs_job_data = {
            'app': self.get_pipeline_id(),
            'inputs': input_json,
            'name': name,
            'tags': tags}
        roslin_qc_outputs_job = [(APIRunCreateSerializer(
            data=roslin_qc_outputs_job_data), input_json)]
        return roslin_qc_outputs_job
