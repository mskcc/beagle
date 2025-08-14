"""""" """""" """""" """""" """""
" ACCESS-Pipeline MSI workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/msi.cwl
""" """""" """""" """""" """""" ""

import os
import json
import logging
from jinja2 import Template
from django.conf import settings
from file_system.models import File
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from runner.models import Port, RunStatus
from runner.operator.access import (
    get_request_id,
    get_request_id_runs,
    create_cwl_file_object,
    find_request_bams,
    is_tumor_bam,
)


logger = logging.getLogger(__name__)

# Todo: needs to work for Nucleo bams as well
TUMOR_SEARCH = "-L0"
NORMAL_SEARCH = "-N0"
STANDARD_BAM_SEARCH = "_cl_aln_srt_MD_IR_FX_BR.bam"
WORKDIR = os.path.dirname(os.path.abspath(__file__))


class AccessV2LegacyMSIOperator(Operator):
    """
    Operator for the ACCESS Legacy Microsatellite Instability workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/msi.cwl

    This Operator will search for ACCESS Standard Bam files based on an IGO Request ID. It will
    also find the matched normals based on the patient ID.
    """

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator.

        :return: list of json_objects
        """
        runs, self.request_id = get_request_id_runs(
            ["access v2 nucleo", "access nucleo"], self.run_ids, self.request_id
        )

        bams = []
        for run in runs:
            bams.append(find_request_bams(run))

        # TUMOR Uncollapsed
        standard_tumor_bams = [b["uncollapsed_bam"] for b in bams if is_tumor_bam(b["fgbio_collapsed_bam"].file_name)]

        # Dictionary that associates tumor bam with standard bam with tumor_sample_id
        sample_tumor_normal = {}
        for standard_tumor_bam in standard_tumor_bams:
            tumor_sample_id = standard_tumor_bam.file_name.split("_cl_aln")[0]
            patient_id = "-".join(tumor_sample_id.split("-")[0:2])

            # Find the matched Normal Standard bam (which could be associated with a different request_id)
            sample_search_start = patient_id + NORMAL_SEARCH
            matched_normal_bam = File.objects.filter(
                file_name__startswith=sample_search_start, file_name__endswith=STANDARD_BAM_SEARCH
            )
            if not len(matched_normal_bam) > 0:
                msg = "No matching standard normal Bam found for patient {}".format(patient_id)
                logger.warning(msg)
                continue

            matched_normal_bam = matched_normal_bam.order_by("-created_date").first()

            sample_tumor_normal[tumor_sample_id] = {"normal": matched_normal_bam, "tumor": standard_tumor_bam}

        sample_inputs = [
            self.construct_sample_inputs(key, value["tumor"], value["normal"])
            for key, value in sample_tumor_normal.items()
        ]

        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        inputs = self.get_sample_inputs()

        return [
            RunCreator(
                **{
                    "name": "ACCESS V2 LEGACY MSI M1: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                        "cmoSampleIds": job["sample_name"],
                        settings.PATIENT_ID_METADATA_KEY: "-".join(job["sample_name"][0].split("-")[0:2]),
                    },
                }
            )
            for i, job in enumerate(inputs)
        ]

    def construct_sample_inputs(self, sample_name, tumor_bam, matched_normal_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())

        sample_names = [sample_name]
        matched_normal_bams = [create_cwl_file_object(matched_normal_bam.path, "iris://")]
        tumor_bams = [create_cwl_file_object(tumor_bam.path, "iris://")]

        input_file = template.render(
            tumor_bams=json.dumps(tumor_bams),
            normal_bams=json.dumps(matched_normal_bams),
            sample_names=json.dumps(sample_names),
        )

        sample_input = json.loads(input_file)
        return sample_input
