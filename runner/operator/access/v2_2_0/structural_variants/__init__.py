import os
import json
import logging

from django.conf import settings
from jinja2 import Template
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import File
from runner.operator.access import (
    get_request_id_runs,
    create_cwl_file_object,
    find_request_bams,
    is_tumor_bam,
)
from runner.models import Pipeline
from datetime import datetime

BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR.bam"
logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))
ACCESS_DEFAULT_SV_NORMAL_FILENAME = "Donor19F21c2206-TP01_ACCESSv2-VAL-20230004R_cl_aln_srt_MD_IR_FX_BR.bam"


class AccessV2LegacySVOperator(Operator):
    """
    Operator for the ACCESS Legacy Structural Variants workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/manta.cwl

    This Operator will search for Standard Bam files based on an IGO Request ID
    """


    def get_sample_inputs(self, runs):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        bams = []
        for run in runs:
            bams.append(find_request_bams(run))

        # Standard TUMOR
        standard_tumor_bams = [b["uncollapsed_bam"] for b in bams if is_tumor_bam(b["uncollapsed_bam"].file_name)]

        sample_ids = [b.file_name.replace(BAM_STEM, "") for b in standard_tumor_bams]
        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_SV_NORMAL_FILENAME)
        normal_bam = normal_bam[0]

        sample_inputs = []
        for i, b in enumerate(standard_tumor_bams):
            sample_input = self.construct_sample_inputs(sample_ids[i], b, normal_bam)
            sample_inputs.append(sample_input)

        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        # output_directory = pipeline.output_directory
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        # If no request_id, get request id from run information
        # else request_id given directly
        runs, self.request_id = get_request_id_runs(
            ["access v2 nucleo", "access nucleo"], self.run_ids, self.request_id
        )
        sample_inputs = self.get_sample_inputs(runs)

        return [
            RunCreator(
                **{
                    "name": "ACCESS V2 LEGACY SV M1: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                        "cmoSampleIds": job["sv_sample_id"],
                        settings.PATIENT_ID_METADATA_KEY: "-".join(job["sv_sample_id"][0].split("-")[0:2]),
                    },
                }
            )
            for i, job in enumerate(sample_inputs)
        ]

    def construct_sample_inputs(self, tumor_sample_id, tumor_bam, normal_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_path = tumor_bam.path.replace("file://", "iris://")
            if not tumor_path.startswith("iris://"):
                tumor_path = "iris://" + tumor_path
            tumor_bams = [{"class": "File", "location": tumor_path}]

            normal_bam = create_cwl_file_object(normal_bam.path, "iris://")

            input_file = template.render(
                tumor_sample_id=tumor_sample_id,
                tumor_sample_names=json.dumps(tumor_sample_names),
                tumor_bams=json.dumps(tumor_bams),
                normal_bam=json.dumps(normal_bam),
            )
            print(input_file)
            sample_input = json.loads(input_file)
            return sample_input
