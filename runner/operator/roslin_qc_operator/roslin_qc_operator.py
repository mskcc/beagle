import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_roslin_qc_outputs import construct_roslin_qc_input
import logging
import json
LOGGER = logging.getLogger(__name__)


class RoslinQcOperator(Operator):
    def get_jobs(self):
        run_ids = self.run_ids
        input_json = construct_roslin_qc_input(run_ids)
        number_of_runs = len(run_ids)
        name = "ROSLIN QC OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])
        tags = {"tumor_sample_names": input_json['tumor_sample_names'],
                "normal_sample_names": input_json['normal_sample_names'],
                "project_prefix": input_json['project_prefix'],
                "number_of_runs": number_of_runs}
        input_json["tags"] = tags
        roslin_qc_outputs_job_data = {
            'app': self.get_pipeline_id(), 'inputs': input_json, 'name': name}
        roslin_qc_outputs_job = [(APIRunCreateSerializer(
            data=roslin_qc_outputs_job_data), input_json)]
        return roslin_qc_outputs_job
