import os
import json
import logging
from jinja2 import Template

from runner.models import Port, RunStatus
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File
from runner.operator.access import get_request_id, get_request_id_runs, create_cwl_file_object



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

    @staticmethod
    def is_tumor(file):
        t_n_timepoint = file.file_name.split('-')[2]
        return not t_n_timepoint[0] == 'N'

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        run_ids = self.run_ids if self.run_ids else [r.id for r in get_request_id_runs(self.request_id)]

        # Get all standard bam ports for these runs
        standard_bam_ports = Port.objects.filter(
            name__in=['standard_bams', 'uncollapsed_bam'],
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )

        standard_tumor_bams = [f for p in standard_bam_ports for f in p.files.all() if self.is_tumor(f)]
        sample_ids = [f.file_name.split('_cl_aln')[0] for f in standard_tumor_bams]

        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_SV_NORMAL_FILENAME)
        if not len(normal_bam) == 1:
            msg = "Incorrect number of files ({}) found for ACCESS SV Default Normal".format(len(normal_bam))
            logger.exception(msg)
            raise Exception(msg)
        normal_bam = normal_bam[0]

        sample_inputs = []
        for i, b in enumerate(standard_tumor_bams):
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
        self.request_id = get_request_id(self.run_ids, self.request_id)
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
                "location": tumor_bam.path.replace('file://', 'juno://')
            }]

            normal_bam = create_cwl_file_object(normal_bam.path)

            input_file = template.render(
                tumor_sample_id=tumor_sample_id,
                tumor_sample_names=json.dumps(tumor_sample_names),
                tumor_bams=json.dumps(tumor_bams),
                normal_bam=json.dumps(normal_bam)
            )

            sample_input = json.loads(input_file)
            return sample_input
