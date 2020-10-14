"""""""""""""""""""""""""""""
" ACCESS-Pipeline MSI
" github.com/mskcc/access-pipeline
"""""""""""""""""""""""""""""

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Port, Run

import json
from jinja2 import Template

def construct_sample_inputs(ports, request_id, group_id):
    with open('runner/operator/access/v1_0_0/msi/input_template.json.jinja2') as file:
        template = Template(file.read())

    sample_names = []
    tumor_bams = []
    normal_bams = []

    for port in ports:
        for row in port.db_value():
            sample_names.append(row["sample_name"])
            tumor_bams.append(row["tumor"])
            tumor_bams.append(row["normal"])

    sample_input = [
        json.loads(
            template.render(
                sample_names=json.dumps(sample_names),
                tumor_bams=json.dumps(tumor_Bams),
                normal_Bams=json.dumps(normal_bams)
            )
        )
    ]

    sample_input = json.loads(input_file)

    return [sample_input]

class AccessLegacyOperator(Operator):
    def get_jobs(self):
        # Not sure what the output of initial ACCESS will look like in Ports.
        # TODO short-circuit if normal doesn't exist
        ports = Port.objects.filter(run_id__in=run_ids)

        sample_inputs = construct_sample_inputs(ports, self.request_id, self.job_group_id)

        number_of_inputs = len(sample_inputs)

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY MSI M1: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {'requestId': self.request_id}
                    }
                ),
                job
             )

            for i, job in enumerate(sample_inputs)
        ]

