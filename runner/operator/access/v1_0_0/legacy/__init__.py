"""""""""""""""""""""""""""""
" ACCESS-Pipeline
" github.com/mskcc/access-pipeline
"""""""""""""""""""""""""""""

from collections import defaultdict
from itertools import groupby
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository

from notifier.events import InputCreationFailedEvent
from notifier.tasks import send_notification

import json
from jinja2 import Template

REQUIRED_META_FIELDS = [
    "cmoSampleName",
    "requestId",
    "tumorOrNormal",
    "sampleId"
]

REQUIRED_INPUT_FIELDS = [
    "fastq1", "fastq2", "add_rg_ID", "add_rg_LB", "adapter", "adapter2"
]

ADAPTER = "GATCGGAAGAGC"
ADAPTER2 = "AGATCGGAAGAGC"
SAMPLE_GROUP_SIZE = 20

"""
This returns a list of keys that are subset of `fields`, that do not exist
in source or exist with an empty value.
"""
def get_missing_fields(source, fields):
    return list(filter(lambda field: field not in source or not source[field], fields))

# In standard order
TITLE_FILE_COLUMNS = [
    'Barcode',
    'Pool',
    'Sample',
    'Collab_ID',
    'Patient_ID',
    'Class',
    'Sample_type',
    'Input_ng',
    'Library_yield',
    'Pool_input',
    'Bait_version',
    'Sex',
    'Barcode_index_1',
    'Barcode_index_2',
    'Lane',
    'Study_ID',
]

def generate_title_file_content(sample_group):
    title_file_content = '\t'.join(TITLE_FILE_COLUMNS) + '\n'
    for sample_pair in sample_group:
        sample = sample_pair[0]
        meta = sample["metadata"]

        pool_info = meta["captureName"]
        if meta['libraryVolume'] and meta['libraryConcentrationNgul']:
            library_yield = meta['libraryVolume'] * meta['libraryConcentrationNgul']
        else:
            library_yield = '-'

        line_content = "\t".join(["{}"] * len(TITLE_FILE_COLUMNS)) + "\n"
        title_file_content += line_content.format(
            meta['barcodeId'] if meta['barcodeId'] else '-',
            pool_info,
            meta['cmoSampleName'],
            meta['investigatorSampleId'],
            meta['patientId'],
            meta['tumorOrNormal'],
            meta['sampleOrigin'],
            meta['dnaInputNg'] if meta['dnaInputNg'] else '-',
            library_yield,
            meta['captureInputNg'] if meta['captureInputNg'] else '-',
            meta['baitSet'],
            meta['sex'] if meta['sex'] in ['Male', 'M', 'Female', 'F'] else '-',
            meta['barcodeIndex'].split('-')[0] if meta['barcodeIndex'] else '-',
            meta['barcodeIndex'].split('-')[1] if meta['barcodeIndex'] else '-',
            # Todo: Get correct lane info
            '1',
            '-'
        )
    return title_file_content.strip()

def construct_sample_inputs(samples, request_id, group_id):
    with open('runner/operator/access/v1_0_0/legacy/input_template.json.jinja2') as file:
        template = Template(file.read())

    sample_inputs = list()
    errors = 0

    # Pair FASTQs
    sample_pairs = list(group_by_sample_id(samples).values())

    # A sample group is a group of 20 PAIRS of samples.
    for sample_group in chunks(sample_pairs, SAMPLE_GROUP_SIZE):
        barcode_ids = []
        tumor_or_normals = []
        cmo_sample_names = []
        patient_ids = []
        add_rg_LBs = [1] * len(sample_group)
        adapters = [ADAPTER] * len(sample_group)
        adapters2 = [ADAPTER2] * len(sample_group)
        title_file_content = generate_title_file_content(sample_group)
        fastq1_files = []
        fastq2_files = []

        for sample_pair in sample_group:
            meta = sample_pair[0]["metadata"]

            missing_fields = get_missing_fields(meta, REQUIRED_META_FIELDS)
            if missing_fields:
                ic_error = InputCreationFailedEvent(
                    "The follwing fields are missing from the input: {}".format(",".join(missing_fields)),
                    group_id,
                    request_id,
                    meta["sampleId"]
                ).to_dict()
                send_notification.delay(ic_error)
                errors += 1
                continue

            cmo_sample_names.append(meta["cmoSampleName"])
            barcode_ids.append(meta["barcodeId"])
            tumor_or_normals.append(meta["tumorOrNormal"])
            patient_ids.append(meta["patientId"])

            fastq1_files.append({
                "class": "File",
                "path": "juno://" + sample_pair[0]["path"]
            })

            fastq2_files.append({
                "class": "File",
                "path": "juno://" + sample_pair[1]["path"]
            })

        input_file = template.render(
            barcode_ids=json.dumps(barcode_ids),
            tumor_or_normals=json.dumps(tumor_or_normals),
            cmo_sample_names=json.dumps(cmo_sample_names),
            add_rg_LBs=json.dumps(add_rg_LBs),
            adapters=json.dumps(adapters),
            adapters2=json.dumps(adapters2),
            fastq1_files=json.dumps(fastq1_files),
            fastq2_files=json.dumps(fastq2_files),
            patient_ids=json.dumps(patient_ids),
            title_file_content=json.dumps(title_file_content),
            request_id=json.dumps(request_id),
        )

        sample_input = json.loads(input_file)

        missing_fields = get_missing_fields(sample_input, REQUIRED_INPUT_FIELDS)
        if missing_fields:
            for sample_pair in sample_group:
                meta = sample_pair[0]["metadata"]
                ic_error = InputCreationFailedEvent(
                    "The following fields are missing from the input: {}".format(",".join(missing_fields)),
                    group_id,
                    request_id,
                    meta["sampleId"]
                ).to_dict()
                send_notification.delay(ic_error)
                errors += 1
            continue

        sample_inputs.append(sample_input)

    return (sample_inputs, errors)

class AccessLegacyOperator(Operator):
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

        (sample_inputs, no_of_errors) = construct_sample_inputs(data, self.request_id, self.job_group_id)
        if no_of_errors:
            return

        number_of_inputs = len(sample_inputs)

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY M1: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {'requestId': self.request_id, 'cmoSampleIds': job["add_rg_ID"]}
                    }
                ),
                job
             )

            for i, job in enumerate(sample_inputs)
        ]


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"]["sampleId"]].append(sample)

    return sample_pairs
