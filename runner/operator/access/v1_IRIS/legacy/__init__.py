"""""" """""" """""" """""" """""
" ACCESS-Pipeline
" github.com/mskcc/access-pipeline
""" """""" """""" """""" """""" ""

import logging
import os
from django.conf import settings
from collections import defaultdict
from runner.models import Port, PortType, Run, RunStatus, Port
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from notifier.events import InputCreationFailedEvent
from notifier.tasks import send_notification
from runner.operator.access import get_request_id_runs
import json
from jinja2 import Template

logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))

REQUIRED_META_FIELDS = [
    settings.SAMPLE_ID_METADATA_KEY,
    "captureName",
    "baitSet",
    settings.CMO_SAMPLE_NAME_METADATA_KEY,
    "tumorOrNormal",
    settings.PATIENT_ID_METADATA_KEY,
    "sex",
    "barcodeId",
    "investigatorSampleId",
]

REQUIRED_INPUT_FIELDS = [
    "fastq1",
    "fastq2",
    "sample_sheet",
    "sample_class",
    "patient_id",
    "add_rg_SM",
    "add_rg_ID",
    "add_rg_LB",
    "add_rg_PU",
    "adapter",
    "adapter2",
]

ADAPTER = "GATCGGAAGAGC"
ADAPTER2 = "AGATCGGAAGAGC"
SAMPLE_GROUP_SIZE = 20

"""
This returns a list of keys that are subset of `fields`, that do not exist
in source or exist with an empty value.
"""


def get_missing_fields(source, fields):
    def validate(field):
        if field not in source:
            return True
        elif not source[field]:
            return True
        elif type(source[field]) == list:
            if not all(source[field]):
                return True
        return False

    return list(filter(validate, fields))


# In standard order
TITLE_FILE_COLUMNS = [
    "Barcode",
    "Pool",
    "Sample",
    "Collab_ID",
    "Patient_ID",
    "Class",
    "Sample_type",
    "Input_ng",
    "Library_yield",
    "Pool_input",
    "Bait_version",
    "Sex",
    "Barcode_index_1",
    "Barcode_index_2",
    "Lane",
    "Study_ID",
]


def generate_title_file_content(sample_group):
    title_file_content = "\t".join(TITLE_FILE_COLUMNS) + "\n"
    for sample_pair in sample_group:
        sample = sample_pair[0]
        meta = sample["metadata"]

        pool_info = meta["captureName"]
        if meta["libraryVolume"] and meta["libraryConcentrationNgul"]:
            library_yield = meta["libraryVolume"] * meta["libraryConcentrationNgul"]
        else:
            library_yield = "-"

        line_content = "\t".join(["{}"] * len(TITLE_FILE_COLUMNS)) + "\n"
        title_file_content += line_content.format(
            meta["barcodeId"] if meta["barcodeId"] else "-",
            pool_info,
            meta[settings.CMO_SAMPLE_NAME_METADATA_KEY],
            meta["investigatorSampleId"],
            meta[settings.PATIENT_ID_METADATA_KEY],
            meta["tumorOrNormal"],
            "Plasma" if meta["tumorOrNormal"] == "Tumor" else "Buffy Coat",
            meta["dnaInputNg"] if meta["dnaInputNg"] else "-",
            library_yield,
            meta["captureInputNg"] if meta["captureInputNg"] else "-",
            meta["baitSet"],
            meta["sex"] if meta["sex"] in ["Male", "M", "Female", "F"] else "-",
            meta["barcodeIndex"].split("-")[0] if meta["barcodeIndex"] else "-",
            meta["barcodeIndex"].split("-")[1] if meta["barcodeIndex"] else "-",
            # Todo: Get correct lane info
            "1",
            "-",
        )
    return title_file_content.strip()


def construct_sample_inputs(samples, request_id, group_id):
    with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
        template = Template(file.read())

    sample_inputs = list()
    errors = 0

    # Pair FASTQs
    sample_pairs = list(group_by_sample_id(samples).values())

    # ABRA will run out of memory if it receives a batch of samples
    # all with the same patient id, so we'll append a count
    # to each sample's patient id
    patient_id_count = defaultdict(int)
    # A sample group is a group of 20 PAIRS of samples.
    group_index = 0
    for sample_group in chunks(sample_pairs, SAMPLE_GROUP_SIZE):
        group_index = group_index + 1
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
        sample_sheets = []

        for sample_pair in sample_group:
            meta = sample_pair[0]["metadata"]

            missing_fields = get_missing_fields(meta, REQUIRED_META_FIELDS)
            if missing_fields:
                ic_error = InputCreationFailedEvent(
                    "The following fields are missing from the metadata: {}".format(",".join(missing_fields)),
                    group_id,
                    request_id,
                    meta[settings.SAMPLE_ID_METADATA_KEY],
                ).to_dict()
                send_notification.delay(ic_error)
                errors += 1
                continue

            patient_id_count[meta[settings.PATIENT_ID_METADATA_KEY]] += 1
            cmo_sample_names.append(meta[settings.CMO_SAMPLE_NAME_METADATA_KEY])
            barcode_ids.append(meta["barcodeId"])
            tumor_or_normals.append(meta["tumorOrNormal"])
            patient_ids.append(
                meta[settings.PATIENT_ID_METADATA_KEY]
                + "_"
                + str(patient_id_count[meta[settings.PATIENT_ID_METADATA_KEY]])
            )

            # Todo: need to add metadata for "Read 1" and "Read 2" to fastq files
            r1_fastq = sample_pair[0] if "_R1_.fastq.gz" in sample_pair[0]["path"] else sample_pair[1]
            r2_fastq = sample_pair[0] if "_R2_.fastq.gz" in sample_pair[0]["path"] else sample_pair[1]

            fastq1_files.append({"class": "File", "location": "iris://" + r1_fastq["path"]})

            fastq2_files.append({"class": "File", "location": "iris://" + r2_fastq["path"]})

            # Todo: Using dummy sample sheets until this requirement is removed from the pipeline
            sample_sheets.append(
                {
                    "class": "File",
                    "location": "iris://"
                    + "/data1/core006/access/production/resources/tools/voyager_resources/SampleSheet.csv",
                }
            )

        input_file = template.render(
            barcode_ids=json.dumps(barcode_ids),
            tumor_or_normals=json.dumps(tumor_or_normals),
            cmo_sample_names=json.dumps(cmo_sample_names),
            add_rg_LBs=json.dumps(add_rg_LBs),
            adapters=json.dumps(adapters),
            adapters2=json.dumps(adapters2),
            fastq1_files=json.dumps(fastq1_files),
            fastq2_files=json.dumps(fastq2_files),
            sample_sheets=json.dumps(sample_sheets),
            patient_ids=json.dumps(patient_ids),
            title_file_content=json.dumps(title_file_content),
            request_id=json.dumps(request_id + "_group_" + str(group_index)),
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
                    meta[settings.SAMPLE_ID_METADATA_KEY],
                ).to_dict()
                send_notification.delay(ic_error)
                errors += 1
            continue

        sample_inputs.append(sample_input)
    return (sample_inputs, errors)


class AccessLegacyOperator(Operator):
    def get_jobs(self):

        run_ids, self.request_id = get_request_id_runs(["fastq-merge"], self.run_ids, self.request_id)
        ports = Port.objects.filter(run_id__in=run_ids, port_type=PortType.OUTPUT)

        data = [
            {"id": f.id, "path": f.path, "file_name": f.file_name, "metadata": f.filemetadata_set.first().metadata}
            for p in ports
            for f in p.files.all()
        ]

        request_id = data[0]["metadata"][settings.REQUEST_ID_METADATA_KEY]
        (sample_inputs, no_of_errors) = construct_sample_inputs(data, request_id, self.job_group_id)

        if no_of_errors:
            return

        number_of_inputs = len(sample_inputs)

        return [
            (
                RunCreator(
                    **{
                        "name": "ACCESS LEGACY COLLAPSING M1: %s, %i of %i" % (request_id, i + 1, number_of_inputs),
                        "app": self.get_pipeline_id(),
                        "inputs": job,
                        "tags": {
                            settings.REQUEST_ID_METADATA_KEY: request_id,
                            "cmoSampleIds": job["add_rg_ID"],
                            "reference_version": "HG19",
                        },
                    }
                )
            )
            for i, job in enumerate(sample_inputs)
        ]


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def group_by_sample_id(samples):
    sample_pairs = defaultdict(list)
    for sample in samples:
        sample_pairs[sample["metadata"][settings.SAMPLE_ID_METADATA_KEY]].append(sample)

    return sample_pairs
