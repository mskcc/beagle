"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
import logging
from jinja2 import Template

from runner.models import Port, Run, RunStatus
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ACCESS_DEFAULT_SV_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_SV_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR.bam'


class AccessLegacySVOperator(Operator):

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        tumor_standard_bams = FileRepository.filter(
            file_type='bam',
            path_regex='_cl_aln_srt_MD_IR_FX_BR.bam',
            metadata={
                'requestId': self.request_id,
                'tumorOrNormal': 'Tumor',
                'igocomplete': True
            }
        )
        sample_ids = [b.metadata['sampleName'] for b in tumor_standard_bams]

        sample_inputs = []
        for i, b in enumerate(tumor_standard_bams):

            sample_input = self.construct_sample_inputs(
                sample_ids[i],
                b
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
                            'cmoSampleIds': job["sv_sample_id"]
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(sample_inputs)
        ]

    def construct_sample_inputs(self, tumor_sample_id, tumor_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": 'juno://' + tumor_bam.file.path
            }]

            normal_bam = FileRepository.filter(
                file_type='bam',
                path_regex=ACCESS_DEFAULT_SV_NORMAL_FILENAME
            )

            if not len(normal_bam) == 1:
                msg = "Incorrect number of files ({}) found for ACCESS SV Default Normal".format(len(normal_bam))
                raise Exception(msg)

            normal_bam = normal_bam[0].file
            normal_bam = {
                "class": "File",
                "location": 'juno://' + normal_bam.path
            }

            input_file = template.render(
                tumor_sample_names=json.dumps(tumor_sample_names),
                tumor_bams=json.dumps(tumor_bams),
                normal_bam=json.dumps(normal_bam)
            )

            sample_input = json.loads(input_file)
            return sample_input
