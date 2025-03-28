import os
import json
import logging

from jinja2 import Template
from django.conf import settings
from collections import defaultdict

from runner.operator.operator import Operator
from runner.operator.helper import pair_samples
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository
from runner.models import Port
from notifier.helper import get_gene_panel
from runner.operator.access import get_request_id_runs, create_cwl_file_object


logger = logging.getLogger(__name__)
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
    settings.CMO_SAMPLE_TAG_METADATA_KEY,
    settings.SAMPLE_ID_METADATA_KEY,
    settings.REQUEST_ID_METADATA_KEY,
    settings.LIBRARY_ID_METADATA_KEY,
]


def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]].append(sample)
    return sample_pairs


def calc_avg(sample_files, field):
    samples_with_field = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(samples_with_field)
    if field_count == 0:
        return 0

    avg = sum([float(s["metadata"][field]) for s in samples_with_field]) / field_count
    return avg


def parse_output_ports(run, port_name):
    port = Port.objects.get(name=port_name, run=run.pk)
    file = port.files.all()[0]
    file = create_cwl_file_object(file.path)
    return file


def construct_sample_inputs(runs, request_id):
    template_f = "input_template.json.jinja2"
    with open(os.path.join(WORKDIR, template_f)) as file:
        template = Template(file.read())

    sample_inputs = []
    for run in runs:
        meta = run.output_metadata
        sample_id = meta[settings.CMO_SAMPLE_NAME_METADATA_KEY]

        fastq_pair = [[parse_output_ports(run, "fastp_read1_output"), parse_output_ports(run, "fastp_read2_output")]]

        input_file = template.render(
            sample_id=sample_id,
            fgbio_fastq_to_bam_input=json.dumps(fastq_pair),
            barcode_id=meta["barcodeId"],
            # Todo: Nucleo needs to take multiple library IDs, so that MD doesn't mark dups incorrectly
            library_id=meta[settings.LIBRARY_ID_METADATA_KEY],
        )

        sample = json.loads(input_file)
        sample_inputs.append((sample, meta))

    return sample_inputs


class AccessV2NucleoTrimOperator(Operator):
    """
    Operator for the ACCESS Nucleo workflow:

    https://github.com/msk-access/nucleo/blob/master/nucleo.cwl

    This Operator will search for fastq files based on an IGO Request ID
    """

    def get_jobs(self):
        runs, self.request_id = get_request_id_runs(["merge-trim"], self.run_ids, self.request_id)
        sample_inputs = construct_sample_inputs(runs, self.request_id)
        number_of_inputs = len(sample_inputs)
        return [
            RunCreator(
                **{
                    "name": "ACCESS V2 Nucleo: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "output_metadata": {key: metadata[key] for key in METADATA_OUTPUT_FIELDS if key in metadata},
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                        "cmoSampleId": metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY],
                    },
                }
            )
            for i, (job, metadata) in enumerate(sample_inputs)
        ]
