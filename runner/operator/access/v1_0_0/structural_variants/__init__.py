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

    def get_tumors_to_run(self):
        """
        Find all runs through collapsing pipeline that have not been run through SNV pipeline

        :return:
        """
        access_duplex_output_ports = Port.objects.filter(
            name='duplex_bams',
            run__app__name='access legacy',
            run__status=RunStatus.COMPLETED
        )
        # Each port is a list, so need a double list comprehension here
        all_access_output_records = [f for p in access_duplex_output_ports for f in p.value]
        # these are port objects, they dont have metadata field
        all_access_completed_samples = [r['sampleId'] for r in all_access_output_records]

        access_snv_runs = Run.objects.filter(status=RunStatus.COMPLETED, app__name='access_legacy_snv')
        already_ran_tumors = [r['tags']['cmoSampleIds'] for r in access_snv_runs]
        already_ran_tumors = [item for sublist in already_ran_tumors for item in sublist]

        tumors_to_run = set(all_access_completed_samples) - set(already_ran_tumors)
        return list(tumors_to_run)

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        tumors_to_run = self.get_tumors_to_run()

        tumor_standard_bams = []

        for i, tumor_sample_id in enumerate(tumors_to_run):

            tumor_standard_bam = FileRepository.filter(
                file_type='bam',
                path_regex='_cl_aln_srt_MD_IR_FX_BR.bam',
                metadata={
                    'tumorOrNormal': 'Tumor',
                    'sampleName': tumor_sample_id
                }
            )
            if not len(tumor_standard_bam) == 1:
                msg = 'Found incorrect number of matching bam files ({}) for sample {}'
                msg = msg.format(len(tumor_standard_bam), tumor_sample_id)
                raise Exception(msg)
            tumor_standard_bam = tumor_standard_bam[0]

            tumor_standard_bams.append(tumor_standard_bam)

        sample_inputs = []
        for i, b in enumerate(tumor_standard_bams):

            sample_input = self.construct_sample_inputs(
                tumors_to_run[i],
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
                            'cmoSampleIds': job["tumor_sample_names"]
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

            print(sample_input)

            return sample_input
