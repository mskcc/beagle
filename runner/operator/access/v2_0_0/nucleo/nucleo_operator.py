import os
import json
import logging

from jinja2 import Template
from collections import defaultdict

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))



def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"]["sampleId"]].append(sample)
    return sample_pairs


def group_by_run(samples):
    samples.sort(key = lambda s: s["path"].split("/")[-1])
    fastqs = zip(samples[::2], samples[1::2])
    return list(fastqs)


def calc_avg(sample_files, field):
    samples_with_field = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(samples_with_field)
    if field_count == 0:
        return 0

    avg = sum([float(s["metadata"][field]) for s in samples_with_field])/field_count
    return avg


def construct_sample_inputs(samples, request_id):
    with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
        template = Template(file.read())

    sample_inputs = list()
    samples_groups = list(group_by_sample_id(samples).values())

    for sample_group in samples_groups:
        meta = sample_group[0]["metadata"]
        meta.update({
            "dnaInputNg": calc_avg(sample_group, "dnaInputNg"),
            "captureInputNg": calc_avg(sample_group, "captureInputNg"),
            "libraryVolume": calc_avg(sample_group, "libraryVolume"),
            "libraryConcentrationNgul": calc_avg(sample_group, "libraryConcentrationNgul"),
            "captureConcentrationNm": calc_avg(sample_group, "captureConcentrationNm"),
            "requestId": request_id
        })

        sample_group = list(sample_group)
        sample_id = sample_group[0]["metadata"]["sampleName"]

        fgbio_fastq_to_bam_input = group_by_run(sample_group)
        fgbio_fastq_to_bam_input = [
            [
                {"class": "File", "location": "juno://" + s[0]["path"]},
                {"class": "File", "location": "juno://" + s[1]["path"]}
            ]
            for s in fgbio_fastq_to_bam_input
        ]

        input_file = template.render(
            sample_id=sample_id,
            fgbio_fastq_to_bam_input=json.dumps(fgbio_fastq_to_bam_input),
            barcode_id=meta['barcodeId'],
            # Todo: Nucleo needs to take multiple library IDs, so that MD doesn't mark dups incorrectly
            library_id=meta['libraryId'],
        )

        sample = json.loads(input_file)
        sample_inputs.append((sample, meta))

    return sample_inputs


class AccessNucleoOperator(Operator):
    """
    Operator for the ACCESS Nucleo workflow:

    https://github.com/msk-access/nucleo/blob/master/nucleo.cwl

    This Operator will search for fastq files based on an IGO Request ID
    """

    def get_jobs(self):
        files = FileRepository.filter(
            queryset=self.files,
            metadata={
                'requestId': self.request_id,
                'igocomplete': True
            }
        )

        data = [
            {
                "id": f.file.id,
                "path": f.file.path,
                "file_name": f.file.file_name,
                "metadata": f.metadata
            } for f in files
        ]

        sample_inputs = construct_sample_inputs(data, self.request_id)
        number_of_inputs = len(sample_inputs)
        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS Nucleo: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'output_metadata': metadata,
                        'tags': {'requestId': self.request_id}}
                ),
                job
             )
            for i, (job, metadata) in enumerate(sample_inputs)
        ]
