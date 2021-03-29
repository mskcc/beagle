import os
import json
import logging
from jinja2 import Template

from runner.operator.operator import Operator
from runner.operator.access import get_request_id_runs, extract_tumor_ports
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File
from runner.models import Port, RunStatus



logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))
TUMOR_OR_NORMAL_SEARCH = '-L0'
SAMPLE_ID_SEP = '_cl_aln'
ACCESS_DEFAULT_SV_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_SV_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR.bam'


class AccessLegacySVOperator(Operator):
    """
    Operator for the ACCESS Legacy Structural Variants workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/manta.cwl

    This Operator will search for Standard Bam files based on an IGO Request ID
    """

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        if self.request_id:
            run_ids = get_request_id_runs(self.request_id)
            run_ids = [r.id for r in run_ids]
        else:
            run_ids = self.run_ids

        # Get all standard bam ports for these runs
        standard_bam_ports = Port.objects.filter(
            name='standard_bams',
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )

        # Filter to only tumor bam files
        standard_tumor_ports = extract_tumor_ports(standard_bam_ports)
        sample_ids = [f['location'].split('/')[-1].split(SAMPLE_ID_SEP)[0] for f in standard_tumor_ports]

        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_SV_NORMAL_FILENAME)
        if not len(normal_bam) == 1:
            msg = "Incorrect number of files ({}) found for ACCESS SV Default Normal".format(len(normal_bam))
            logger.exception(msg)
            raise Exception(msg)
        normal_bam = normal_bam[0]

        sample_inputs = []
        for i, b in enumerate(standard_tumor_ports):
            sample_input = self.construct_sample_inputs(
                sample_ids[i],
                b,
                normal_bam
            )
            sample_inputs.append(sample_input)

        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        sample_inputs = self.get_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY SV M1: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleIds': job["sv_sample_id"],
                            'patientId': '-'.join(job["sv_sample_id"][0].split('-')[0:2])
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(sample_inputs)
        ]

    def construct_sample_inputs(self, tumor_sample_id, tumor_bam, normal_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": tumor_bam['location'].replace('file://', 'juno://')
            }]

            normal_bam = {
                "class": "File",
                "location": 'juno://' + normal_bam.path
            }

            input_file = template.render(
                tumor_sample_id=tumor_sample_id,
                tumor_sample_names=json.dumps(tumor_sample_names),
                tumor_bams=json.dumps(tumor_bams),
                normal_bam=json.dumps(normal_bam)
            )

            sample_input = json.loads(input_file)
            return sample_input
