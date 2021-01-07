import os
import json
import logging
from jinja2 import Template

from runner.operator.operator import Operator
from runner.operator.access import get_request_id_runs
from runner.models import Port, Run, RunStatus
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


logger = logging.getLogger(__name__)

SAMPLE_ID_SEP = '_cl_aln'
TUMOR_SEARCH = '-L0'
NORMAL_SEARCH = '-N0'
WORKDIR = os.path.dirname(os.path.abspath(__file__))
ACCESS_DEFAULT_CNV_NORMAL_FILENAME = r'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam$'


class AccessLegacyCNVOperator(Operator):
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
        request_id_runs = get_request_id_runs(self.request_id)

        # Get all unfiltered bam ports for these runs
        unfiltered_bam_ports = Port.objects.filter(
            name='unfiltered_bams',
            run__id__in=[r.id for r in request_id_runs]
        )

        # Filter to only tumor bam files
        # Todo: Use separate metadata fields for Tumor / sample ID designation instead of file name
        unfiltered_tumor_bam_files = [f for p in unfiltered_bam_ports for f in p.value if TUMOR_SEARCH in f['location'].split('/')[-1]]
        sample_ids_to_run = [f['location'].split('/')[-1].split(SAMPLE_ID_SEP)[0] for f in unfiltered_tumor_bam_files]

        tumor_bams = []
        sample_sexes = []

        for i, tumor_sample_id in enumerate(sample_ids_to_run):

            # Locate the Unfiltered Tumor BAM
            sample_regex = r'{}.*_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam$'.format(tumor_sample_id)
            unfiltered_tumor_bam = FileRepository.filter(path_regex=sample_regex)
            if len(unfiltered_tumor_bam) < 1:
                msg = 'WARNING: Could not find unfiltered tumor bam file for sample {}' \
                      'We will skip running this sample.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
                raise Exception(msg)
            if len(unfiltered_tumor_bam) > 1:
                msg = 'WARNING: Found more than one unfiltered bam file for tumor sample {}. ' \
                      'We will choose the most recently-created one for this run.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
            # Take the latest one
            unfiltered_tumor_bam = unfiltered_tumor_bam.order_by('-created_date').first()

            # Use the initial fastq metadata to get the sex of the sample
            tumor_fastqs = FileRepository.filter(
                file_type='fastq',
                metadata={
                    'tumorOrNormal': 'Tumor',
                    'sampleName': tumor_sample_id
                }
            )
            sample_sex = tumor_fastqs[0].metadata['sex']
            tumor_bams.append(unfiltered_tumor_bam)
            sample_sexes.append(sample_sex)

        sample_inputs = [self.construct_sample_inputs(
            tumor_bams[i],
            sample_sexes[i]
        ) for i in range(0, len(tumor_bams))]

        return sample_inputs, sample_ids_to_run

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
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
                            'cmoSampleIds': sample_ids[i]
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

            tumor_sample_list = tumor_bam.file.path + '\t' + sample_sex

            input_file = template.render(
                tumor_sample_list_content=json.dumps(tumor_sample_list),
            )

            sample_input = json.loads(input_file)
            return sample_input
