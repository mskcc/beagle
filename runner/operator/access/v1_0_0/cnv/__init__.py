import os
import json
import logging
from jinja2 import Template

from runner.models import Port, RunStatus
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository
from runner.operator.access import get_request_id, get_request_id_runs


logger = logging.getLogger(__name__)

SAMPLE_ID_SEP = '_cl_aln'
TUMOR_SEARCH = '-L0'
NORMAL_SEARCH = '-N0'
WORKDIR = os.path.dirname(os.path.abspath(__file__))
ACCESS_DEFAULT_CNV_NORMAL_FILENAME = r'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam$'
UNFILTERED_BAM_SEARCH = '_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam'


class AccessLegacyCNVOperator(Operator):
    """
    Operator for the ACCESS Legacy Copy Number Variants workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/call_cnv.cwl

    This Operator will search for ACCESS Unfiltered Bam files based on an IGO Request ID.
    """

    @staticmethod
    def is_tumor(file):
        t_n_timepoint = file.file_name.split('-')[2]
        return not t_n_timepoint[0] == 'N'

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator.

        :return: list of json_objects
        """
        run_ids = self.run_ids if self.run_ids else [r.id for r in get_request_id_runs(self.request_id)]

        # Get all unfiltered bam ports for these runs
        unfiltered_bam_ports = Port.objects.filter(
            name__in=['unfiltered_bams', 'fgbio_collapsed_bam'],
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )

        unfiltered_tumor_bams = [f for p in unfiltered_bam_ports for f in p.files.all() if self.is_tumor(f)]

        sample_ids = []
        tumor_bams = []
        sample_sexes = []

        for tumor_bam in unfiltered_tumor_bams:
            sample_id = tumor_bam.file_name.split('_cl_aln')[0]
            # Use the initial fastq metadata to get the sex of the sample
            # Todo: Need to store this info on the bams themselves
            tumor_fastqs = FileRepository.filter(
                file_type='fastq',
                metadata={
                    'tumorOrNormal': 'Tumor',
                    'sampleName': sample_id
                }
            )
            sample_sex = tumor_fastqs[0].metadata['sex']
            tumor_bams.append(tumor_bam)
            sample_sexes.append(sample_sex)
            sample_ids.append(sample_id)

        sample_inputs = [self.construct_sample_inputs(
            tumor_bams[i],
            sample_sexes[i]
        ) for i in range(0, len(tumor_bams))]

        return sample_inputs, sample_ids

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        self.request_id = get_request_id(self.run_ids, self.request_id)
        inputs, sample_ids = self.get_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY CNV M1: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleIds': sample_ids[i],
                            'patientId': '-'.join(sample_ids[i].split('-')[0:2])
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(inputs)
        ]

    def construct_sample_inputs(self, tumor_bam, sample_sex):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_list = tumor_bam.path + '\t' + sample_sex
            # Todo: need this to work with Nucleo bams:
            tumor_sample_id = tumor_bam.file_name.split('_cl_aln_srt_MD_IR_FX_BR')[0]

            input_file = template.render(
                tumor_sample_id=tumor_sample_id,
                tumor_sample_list_content=json.dumps(tumor_sample_list),
            )

            sample_input = json.loads(input_file)
            return sample_input
