from collections import defaultdict
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer

import json
import pprint
from jinja2 import Template

def construct_sample_inputs(request_id, samples):
    with open('runner/operator/access/fastq_to_bam/input_template.json.jinja2') as file:
        template = Template(file.read())

    sample_inputs = list()
    for sample in samples:
        meta = sample["metadata"]

        input_file = template.render(
            cmo_sample_name=meta["cmoSampleName"],
            tumor_type=meta["specimenType"],
            igo_id=meta["igoId"],
            patient_id=meta["cmoPatientId"],

            barcode_index=libraries[0]["barcodeIndex"],

            flowcell_id=libraries[0]["runs"][0]["flowCellId"],
            run_date=libraries[0]["runs"][0]["runDate"],

            request_id=request_id
        )

        sample = json.loads(input_file)

        sample["fastq1"] = []
        sample["fastq2"] = []


        for library in meta["libraries"]:
            for run in library["runs"]:
                samples["fastq1"].append(
                    {
                        "class": "File",
                        "path": "juno://" + run["fastqs"][0]
                    }
                )
                samples["fastq2"].append(
                    {
                        "class": "File",
                        "path": "juno://" + run["fastqs"][1]
                    }
                )

        sample_inputs.append(sample)

    return sample_inputs

class AccessFastqToBamOperator(Operator):
    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__request_id=self.request_id, filemetadata__metadata__igocomplete=True).all()

        data = [
            {
                "id": f.id,
                "path": f.path,
                "file_name": f.file_name,
                "metadata": f.filemetadata_set.first().metadata
            } for f in files
        ]

        sample_inputs = construct_sample_inputs(self.request_id, data)

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
