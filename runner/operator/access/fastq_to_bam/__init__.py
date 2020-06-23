from collections import defaultdict
from itertools import groupby
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository

import json
from jinja2 import Template

def construct_sample_inputs(samples):
    with open('runner/operator/access/fastq_to_bam/input_template.json.jinja2') as file:
        template = Template(file.read())

    sample_inputs = list()
    for sample_id, sample_group in groupby(samples, lambda x: x["metadata"]["sampleId"]):
        sample_group = list(sample_group)
        meta = sample_group[0]["metadata"]

        input_file = template.render(
            cmo_sample_name=meta["sampleName"],
            tumor_type=meta["specimenType"],
            igo_id=sample_id,
            patient_id=meta["patientId"],

            barcode_index=meta["barcodeIndex"],

            flowcell_id=meta["flowCellId"],
            run_date=meta["runDate"],

            request_id=meta["requestId"],

            fastq1_path="juno://" + sample_group[0]["path"],
            fastq2_path="juno://" + sample_group[1]["path"],
        )

        sample = json.loads(input_file)

        sample_inputs.append(sample)

    return sample_inputs

class AccessFastqToBamOperator(Operator):
    def get_jobs(self):
        files = FileRepository.filter(queryset=self.files,
                                      metadata={'requestId': self.request_id,
                                                'igocomplete': True})
        data = [
            {
                "id": f.file.id,
                "path": f.file.path,
                "file_name": f.file.file_name,
                "metadata": f.metadata
            } for f in files
        ]

        sample_inputs = construct_sample_inputs(data)

        number_of_inputs = len(sample_inputs)

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS M1: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {'requestId': self.request_id}}
                ),
                job
             )

            for i, job in enumerate(sample_inputs)
        ]
