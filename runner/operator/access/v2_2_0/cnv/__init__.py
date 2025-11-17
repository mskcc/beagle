import os
import json
import logging
from jinja2 import Template

from django.conf import settings
from runner.models import Port, RunStatus
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository
from runner.operator.access import get_request_id_runs, find_request_bams, is_tumor_bam


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))


class AccessV2LegacyCNVOperator(Operator):
    """
    Operator for the ACCESS Legacy Copy Number Variants workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/call_cnv.cwl

    This Operator will search for ACCESS Unfiltered Bam files based on an IGO Request ID.
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

        # TUMOR Unfiltered
        unfiltered_tumor_bams = [
            b["fgbio_collapsed_bam"] for b in bams if is_tumor_bam(b["fgbio_collapsed_bam"].file_name)
        ]

        sample_ids = []
        tumor_bams = []
        sample_sexes = []

        for tumor_bam in unfiltered_tumor_bams:
            sample_id = tumor_bam.file_name.split("_cl_aln")[0]
            # Use the initial fastq metadata to get the sex of the sample
            # Todo: Need to store this info on the bams themselves
            tumor_fastqs = FileRepository.filter(
                file_type="fastq",
                metadata={"tumorOrNormal": "Tumor", settings.CMO_SAMPLE_NAME_METADATA_KEY: sample_id},
                filter_redact=True,
            )
            sample_sex = tumor_fastqs[0].metadata["sex"]
            tumor_bams.append(tumor_bam)
            sample_sexes.append(sample_sex)
            sample_ids.append(sample_id)

        sample_inputs = [
            self.construct_sample_inputs(tumor_bams[i], sample_sexes[i]) for i in range(0, len(tumor_bams))
        ]

        return sample_inputs, sample_ids

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        inputs, sample_ids = self.get_sample_inputs()

        return [
            (
                RunCreator(
                    **{
                        "name": "ACCESS V2 LEGACY CNV M1: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                        "app": self.get_pipeline_id(),
                        "inputs": job,
                        "tags": {
                            settings.REQUEST_ID_METADATA_KEY: self.request_id,
                            "cmoSampleIds": sample_ids[i],
                            settings.PATIENT_ID_METADATA_KEY: "-".join(sample_ids[i].split("-")[0:2]),
                        },
                    }
                )
            )
            for i, job in enumerate(inputs)
        ]

    def construct_sample_inputs(self, tumor_bam, sample_sex):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())

            tumor_sample_list = tumor_bam.path + "\t" + sample_sex
            tumor_sample_id = tumor_bam.file_name.split("_cl_aln_srt_MD_IR_FX_BR")[0]

            input_file = template.render(
                tumor_sample_id=tumor_sample_id,
                tumor_sample_list_content=json.dumps(tumor_sample_list),
            )
            print(input_file)
            sample_input = json.loads(input_file)
            return sample_input
