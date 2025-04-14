import os
import json
from jinja2 import Template
from collections import defaultdict
from itertools import groupby
from django.conf import settings
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository
import re

WORKDIR = os.path.dirname(os.path.abspath(__file__))


METADATA_OUTPUT_FIELDS = [
    "barcodeId",
    settings.CMO_SAMPLE_NAME_METADATA_KEY,
    "investigatorSampleId",
    settings.PATIENT_ID_METADATA_KEY,
    "tumorOrNormal",
    "sampleOrigin",
    "dnaInputNg",
    "captureInputNg",
    "baitSet",
    "sex",
    "barcodeIndex",
    "libraryVolume",
    "captureName",
    "libraryConcentrationNgul",
    "captureConcentrationNm",
    settings.SAMPLE_ID_METADATA_KEY,
    settings.REQUEST_ID_METADATA_KEY,
    settings.LIBRARY_ID_METADATA_KEY,
]


def construct_inputs(samples, request_id):
    with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
        template = Template(file.read())

    samples = list(group_by_sample_id(samples).values())

    inputs = list()
    for sample_files in samples:
        fastqs = group_by_fastq(sample_files)
        metadata = sample_files[0]["metadata"]
        metadata.update(
            {
                "dnaInputNg": calc_avg(sample_files, "dnaInputNg"),
                "captureInputNg": calc_avg(sample_files, "captureInputNg"),
                "libraryVolume": calc_avg(sample_files, "libraryVolume"),
                "libraryConcentrationNgul": calc_avg(sample_files, "libraryConcentrationNgul"),
                "captureConcentrationNm": calc_avg(sample_files, "captureConcentrationNm"),
                settings.REQUEST_ID_METADATA_KEY: request_id,
            }
        )
        merge_fastq_fastq1 = [{"class": "File", "location": "juno://" + fastq["path"]} for fastq in fastqs["R1"]]

        merge_fastq_fastq2 = [{"class": "File", "location": "juno://" + fastq["path"]} for fastq in fastqs["R2"]]

        input_file = template.render(
            merge_fastq_fastq1=json.dumps(merge_fastq_fastq1),
            merge_fastq_fastq2=json.dumps(merge_fastq_fastq2),
        )
        inputs.append((json.loads(input_file), metadata))

    return inputs


class AccessV2MergeTrimOperator(Operator):
    def get_jobs(self):
        files = FileRepository.filter(
            queryset=self.files,
            metadata={settings.REQUEST_ID_METADATA_KEY: self.request_id, settings.IGO_COMPLETE_METADATA_KEY: True},
            filter_redact=True,
        )
        data = [
            {"id": f.file.id, "path": f.file.path, "file_name": f.file.file_name, "metadata": f.metadata} for f in files
        ]

        inputs = construct_inputs(data, self.request_id)

        number_of_inputs = len(inputs)

        return [
            RunCreator(
                **{
                    "name": "ACCESS V2 Merge Trim: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                    "app": self.get_pipeline_id(),
                    "output_metadata": {key: metadata[key] for key in METADATA_OUTPUT_FIELDS if key in metadata},
                    "inputs": job,
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                        settings.CMO_SAMPLE_NAME_METADATA_KEY: metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY],
                    },
                }
            )
            for i, (job, metadata) in enumerate(inputs)
        ]


def calc_avg(sample_files, field):
    fields = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(fields)
    if field_count == 0:
        return 0

    return sum([float(s["metadata"][field]) for s in fields]) / field_count


def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]].append(sample)

    return sample_pairs


def group_by_fastq(samples):
    fastqs = defaultdict(list)
    for s1 in samples:
        if "_R1_" in s1["path"]:
            fastqs["R1"].append(s1["path"])
            R2_path = s1["path"].replace("_R1_","_R2_")
            for s2 in samples:
                if s2["path"] == R2_path :
                    fastqs["R2"].append(s2["path"])
    return fastqs
