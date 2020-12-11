import os
from collections import defaultdict
from itertools import groupby
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository

import json
from jinja2 import Template

WORKDIR = os.path.dirname(os.path.abspath(__file__))


METADATA_OUTPUT_FIELDS = [
    'barcodeId',
    'sampleName',
    'investigatorSampleId',
    'patientId',
    'tumorOrNormal',
    'sampleOrigin',
    'dnaInputNg',
    'captureInputNg',
    'baitSet',
    'sex',
    'barcodeIndex',
    'libraryVolume',
    'captureName',
    'libraryConcentrationNgul',
    'captureConcentrationNm'
]
def construct_inputs(samples):
    with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
        template = Template(file.read())


    samples = list(group_by_sample_id(samples).values())

    inputs = list()
    for sample_files in samples:
        fastqs = group_by_fastq(sample_files)
        metadata = sample_files[0]["metadata"]
        metadata.update({
            "dnaInputNg": calc_avg(sample_files, "dnaInputNg"),
            "captureInputNg": calc_avg(sample_files, "captureInputNg"),
            "libraryVolume": calc_avg(sample_files, "libraryVolume"),
            "libraryConcentrationNgul": calc_avg(sample_files, "libraryConcentrationNgul"),
            "captureConcentrationNm": calc_avg(sample_files, "captureConcentrationNm")

        })

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

        inputs.append((json.loads(input_file), metadata))

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
                        'output_metadata': {key: metadata[key] for key in METADATA_OUTPUT_FIELDS if
                                            key in metadata},
                        'inputs': job,
                        'tags': {'requestId': self.request_id, 'sampleId': metadata["sampleId"]}}
                ),
                job
             )

            for i, (job, metadata) in enumerate(inputs)
        ]

def calc_avg(sample_files, field):
    fields = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(fields)
    if field_count == 0:
        return 0

    return sum([float(s["metadata"][field]) for s in fields])/field_count

def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"]["sampleId"]].append(sample)

    return sample_pairs

def group_by_fastq(samples):
    fastqs = defaultdict(list)
    samples.sort(key = lambda s: s["path"].split("/")[-1])
    for sample in samples:
        if '_R2_' in sample["path"]:
            fastqs["R2"].append(sample)
        else:
            fastqs["R1"].append(sample)

    return fastqs
