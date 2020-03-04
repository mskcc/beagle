import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_copy_outputs import construct_copy_outputs_input


class CopyOutputsOperator(Operator):
    def get_jobs(self):
        run_ids = self.run_ids
        input_json = construct_copy_outputs_input(run_ids)
        number_of_runs = len(run_ids)
        name = "ROSLIN COPY OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])
        copy_outputs_job_data = {
            'app': self.get_pipeline_id(), 'inputs': input_json, 'name': name}
        copy_outputs_job = [(APIRunCreateSerializer(
            data=copy_outputs_job_data), input_json)]
        return copy_outputs_job
