import os
import json
import logging
from jinja2 import Template

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository
from runner.models import Run, Port, RunStatus



logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))
TUMOR_OR_NORMAL_SEARCH = '-L0'
SAMPLE_ID_SEP = '_cl_aln'
ACCESS_DEFAULT_SV_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_SV_NORMAL_FILENAME = r'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR.bam$'


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
        # Get the latest completed bam generation run for the given request ID
        group_id = Run.objects.filter(
            tags__requestId=self.request_id,
            app__name='access legacy',
            status=RunStatus.COMPLETED
        ).order_by('-finished_date').first().job_group

        request_id_runs = Run.objects.filter(
            job_group=group_id,
            status=RunStatus.COMPLETED
        )

        # Get all standard bam ports for these runs
        standard_bam_ports = Port.objects.filter(
            name='standard_bams',
            run__id__in=[r.id for r in request_id_runs],
            run__status=RunStatus.COMPLETED
        )

        # Filter to only tumor bam files
        # Todo: Use separate metadata fields for Tumor / sample ID designation instead of file name
        standard_tumor_bam_files = [f for p in standard_bam_ports for f in p.value if TUMOR_OR_NORMAL_SEARCH in f['location'].split('/')[-1]]
        sample_ids = [f['location'].split('/')[-1].split(SAMPLE_ID_SEP)[0] for f in standard_tumor_bam_files]

        sample_inputs = []
        for i, b in enumerate(standard_tumor_bam_files):
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
                "location": tumor_bam['location'].replace('file://', 'juno://')
            }]

            normal_bam = FileRepository.filter(
                file_type='bam',
                path_regex=ACCESS_DEFAULT_SV_NORMAL_FILENAME
            )

            if not len(normal_bam) == 1:
                msg = "Incorrect number of files ({}) found for ACCESS SV Default Normal".format(len(normal_bam))
                logger.exception(msg)
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
