import os
import json
import logging

from jinja2 import Template
from django.conf import settings
from collections import defaultdict

from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository


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
runIds = {"NovaSeq": "RUTH_0275", "NovaSeq_X": "FAUCI_0070", "NovaSeq_X_max": "FAUCI_0070"}
maxReads = {"NovaSeq": 95, "NovaSeq_X": 95, "NovaSeq_X_max": 0}


def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]].append(sample)
    return sample_pairs


def group_by_run(samples):
    samples.sort(key=lambda s: s["path"].split("/")[-1])
    fastqs = zip(samples[::2], samples[1::2])
    return list(fastqs)


def calc_avg(sample_files, field):
    samples_with_field = list(filter(lambda s: field in s["metadata"] and s["metadata"][field], sample_files))
    field_count = len(samples_with_field)
    if field_count == 0:
        return 0

    avg = sum([float(s["metadata"][field]) for s in samples_with_field]) / field_count
    return avg


def construct_sample_inputs(samples, request_id, seq):
    with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
        template = Template(file.read())

    sample_inputs = list()
    samples_groups = list(group_by_sample_id(samples).values())

    for sample_group in samples_groups:
        meta = sample_group[0]["metadata"]
        logger.debug('BEFORE UPDATE OF DICTIONARY WITH METADATA')
        logger.debug('SEE VALUES:')
        logger.debug(calc_avg(sample_group, "dnaInputNg"))
        logger.debug(calc_avg(sample_group, "captureInputNg"))
        logger.debug(calc_avg(sample_group, "libraryVolume"))
        logger.debug(calc_avg(sample_group, "libraryConcentrationNgul"))
        logger.debug(calc_avg(sample_group, "captureConcentrationNm"))
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
        logger.debug('AFTER UPDATE OF DICTIONARY WITH METADATA')

        sample_group = list(sample_group)
        sample_id = sample_group[0]["metadata"][settings.CMO_SAMPLE_NAME_METADATA_KEY]

        fgbio_fastq_to_bam_input = group_by_run(sample_group)
        fgbio_fastq_to_bam_input = [
            [
                {"class": "File", "location": "juno://" + s[0]["path"]},
                {"class": "File", "location": "juno://" + s[1]["path"]},
            ]
            for s in fgbio_fastq_to_bam_input
        ]
        logger.info('BEFORE RENDER')
        fastp_max_len_read1 = maxReads[seq]
        fastp_max_len_read2 = maxReads[seq]
        input_file = template.render(
            sample_id=sample_id,
            fgbio_fastq_to_bam_input=json.dumps(fgbio_fastq_to_bam_input),
            barcode_id=meta["barcodeId"],
            # Todo: Nucleo needs to take multiple library IDs, so that MD doesn't mark dups incorrectly
            library_id=meta[settings.LIBRARY_ID_METADATA_KEY],
        )
        logger.info('AFTER RENDER')
        sample = json.loads(input_file)
        logger.debug('BEFORE UPDATE OF DICTIONARY WITH READ LENGTH')
        logger.debug('READ LENGTH VALUES:')
        logger.debug(fastp_max_len_read1)
        logger.debug(fastp_max_len_read2)
        sample["fastp_max_len_read1"] = fastp_max_len_read1
        sample["fastp_max_len_read2"] = fastp_max_len_read2
        sample_inputs.append((sample, meta))
        logger.debug('BEFORE UPDATE OF DICTIONARY WITH READ LENGTH')

    return sample_inputs


class AccessNucleoOperator(Operator):
    """
    Operator for the ACCESS Nucleo workflow:

    https://github.com/msk-access/nucleo/blob/master/nucleo.cwl

    This Operator will search for fastq files based on an IGO Request ID
    """

    def get_jobs(self, seq):
        logger.info('function set up')
        request_id = self.request_id.split("_NovaSeq", 1)[0]
        # files = FileRepository.filter(file_group="b54d035d-f63c-4ea8-86fb-9dbc976bb7fe").all()
        files = FileRepository.filter(
            queryset=self.files,
            metadata={settings.REQUEST_ID_METADATA_KEY: request_id, settings.IGO_COMPLETE_METADATA_KEY: True},
        )
        runId = runIds[seq]
        files = files.filter(metadata__runId=runId)
        data = [
            {"id": f.file.id, "path": f.file.path, "file_name": f.file.file_name, "metadata": f.metadata} for f in files
        ]
        logger.info('before construct sample inputs')
        sample_inputs = construct_sample_inputs(data, request_id, seq)
        logger.info('after construct sample inputs')
        number_of_inputs = len(sample_inputs)
        for i, (job, metadata) in enumerate(sample_inputs):
            if metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] == 'C-P7VRR4-N004-d05':
                # File path
                file_path = "/srv/services/beagle_dev/job.json"
                # Write JSON object to file
                with open(file_path, "w") as json_file:
                    json.dump(job, json_file)
                logger.debug("PLEASE FIND ME SAMPLE: C-P7VRR4-N004-d05")
                logger.debug(json.dumps(job, indent=4))
                logger.debug(self.request_id)


        return [
            RunCreator(
                **{
                    "name": "ACCESS Nucleo: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
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
