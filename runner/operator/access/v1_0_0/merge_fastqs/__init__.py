import os
from collections import defaultdict
from itertools import groupby
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository

import json
from jinja2 import Template

WORKDIR = os.path.dirname(os.path.abspath(__file__))

def construct_inputs(samples):
    with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
        template = Template(file.read())


    sample_files = list(group_by_sample_id(samples).values())

    inputs = list()
    for sample_file in sample_files:
        fastqs = group_by_fastq(sample_file)

        fastq1s = [{
            "class": "File",
            "location": "juno://" + fastq["path"]
        } for fastq in fastqs["R1"]]

        fastq2s = [{
            "class": "File",
            "location": "juno://" + fastq["path"]
        } for fastq in fastqs["R2"]]

        input_file = template.render(
            fastq1_files=json.dumps(fastq1s),
            fastq2_files=json.dumps(fastq2s),
        )

        inputs.append(json.loads(input_file))

    return inputs 

class AccessLegacyFastqMergeOperator(Operator):
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

        inputs = construct_inputs(data)

        number_of_inputs = len(inputs)

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "LEGACY FASTQ Merge: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                        'app': self.get_pipeline_id(),
                        'output_metadata': {

                        },
                        'inputs': job,
                        'tags': {'requestId': self.request_id}}
                ),
                job
             )

            for i, job in enumerate(inputs)
        ]

def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"]["sampleId"]].append(sample)

    return sample_pairs

def group_by_fastq(samples):
    fastqs = defaultdict(list)
    for sample in samples:
        if '_R2_' in sample["path"]:
            fastqs["R2"].append(sample)
        else:
            fastqs["R1"].append(sample)

    return fastqs

