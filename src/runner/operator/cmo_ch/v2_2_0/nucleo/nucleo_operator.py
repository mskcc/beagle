import os
import json
import logging

from jinja2 import Template
from collections import defaultdict

from runner.operator.operator import Operator
from runner.operator.helper import pair_samples
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository
from django.conf import settings

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
]


def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        print(sample["metadata"])
        sample_pairs[sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]].append(sample)
    return sample_pairs


def pair_samples(fastqs):
    """
    pair sample fastqs based on the delivery directory.

    Parameters:
        fastqs (list): A list of sample fastq files.

    Returns:
        list: A list of tuples containing paired fastqs for a sample
    """
    sample_pairs = []
    expected_pair = set(["R1", "R2"])
    # match R1 and R2 based on delivery directory
    # sorting on file names is not enough as they are non-unique
    for i, fastq in enumerate(fastqs):
        dir = "/".join(fastq["path"].split("_R")[0:-1])
        for compare in fastqs[i + 1 :]:
            compare_dir = "/".join(compare["path"].split("_R")[0:-1])
            if dir == compare_dir:
                # check if R1 and R2 are present
                r_check = set([fastq["metadata"]["R"], compare["metadata"]["R"]])
                if r_check.issubset(expected_pair):
                    # Keep ordering consistent
                    if fastq["metadata"]["R"] == "R1":
                        sample_pairs.append((fastq, compare))
                    else:
                        sample_pairs.append((compare, fastq))
                else:
                    sample_name = fastq["metadata"]["cmoSampleName"]
                    raise Exception(f"Improper pairing for: {sample_name}")
    return sample_pairs


def calc_avg(sample_files, field):
    samples_with_field = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(samples_with_field)
    if field_count == 0:
        return 0

    avg = sum([float(s["metadata"][field]) for s in samples_with_field]) / field_count
    return avg


def construct_sample_inputs(samples, request_id):
    with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
        template = Template(file.read())

    sample_inputs = list()
    samples_groups = list(group_by_sample_id(samples).values())

    for sample_group in samples_groups:
        meta = sample_group[0]["metadata"]
        meta.update(
            {
                "dnaInputNg": calc_avg(sample_group, "dnaInputNg"),
                "captureInputNg": calc_avg(sample_group, "captureInputNg"),
                "libraryVolume": calc_avg(sample_group, "libraryVolume"),
                "libraryConcentrationNgul": calc_avg(sample_group, "libraryConcentrationNgul"),
                "captureConcentrationNm": calc_avg(sample_group, "captureConcentrationNm"),
                settings.REQUEST_ID_METADATA_KEY: request_id,
            }
        )

        sample_group = list(sample_group)
        sample_id = sample_group[0]["metadata"][settings.CMO_SAMPLE_NAME_METADATA_KEY]

        fgbio_fastq_to_bam_input = pair_samples(sample_group)
        fgbio_fastq_to_bam_input = [
            [
                {"class": "File", "location": "iris://" + s[0]["path"]},
                {"class": "File", "location": "iris://" + s[1]["path"]},
            ]
            for s in fgbio_fastq_to_bam_input
        ]

        input_file = template.render(
            sample_id=sample_id,
            fgbio_fastq_to_bam_input=json.dumps(fgbio_fastq_to_bam_input),
            barcode_id=meta["barcodeId"],
            # Todo: Nucleo needs to take multiple library IDs, so that MD doesn't mark dups incorrectly
            library_id=meta[settings.LIBRARY_ID_METADATA_KEY],
        )

        sample = json.loads(input_file)
        sample_inputs.append((sample, meta))

    return sample_inputs


class CMOCHNucleoOperator(Operator):
    """
    Operator for the CMO-CH Nucleo workflow:

    https://github.com/msk-access/nucleo/blob/master/nucleo.cwl

    This Operator will search for fastq files based on an IGO Request ID
    """

    def get_jobs(self):
        files = FileRepository.filter(
            queryset=self.files,
            metadata={settings.REQUEST_ID_METADATA_KEY: self.request_id, settings.IGO_COMPLETE_METADATA_KEY: True},
        )

        data = [
            {"id": f.file.id, "path": f.file.path, "file_name": f.file.file_name, "metadata": f.metadata} for f in files
        ]

        sample_inputs = construct_sample_inputs(data, self.request_id)
        number_of_inputs = len(sample_inputs)
        return [
            RunCreator(
                **{
                    "name": "CMO-CH Nucleo: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
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
