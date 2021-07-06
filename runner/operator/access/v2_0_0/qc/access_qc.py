import os
import json
import logging

from jinja2 import Template

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.operator.access import get_most_recent_files_for_request


logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))




class AccessQCOperator(Operator):
    """
    Operator for the ACCESS QC workflow:

    https://github.com/msk-access/access_qc_generation/blob/master/access_qc.cwl

    This Operator will search for Nucleo Bam files based on an IGO Request ID
    """
    def get_jobs(self):

        sample_inputs = self.construct_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS QC: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'output_metadata': metadata,
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleId': job['sample_name']
                        }
                    }
                ),
                job
             )
            for i, (job, metadata) in enumerate(sample_inputs)
        ]

    def construct_sample_inputs(self):
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

        fgbio_postprocessing_simplex_bam = get_most_recent_files_for_request(self.request_id, self.app, name='fgbio_postprocessing_simplex_bam')
        fgbio_filter_consensus_reads_duplex_bam = get_most_recent_files_for_request(self.request_id, self.app, name='fgbio_filter_consensus_reads_duplex_bam')
        fgbio_collapsed_bam = get_most_recent_files_for_request(self.request_id, self.app, name='fgbio_collapsed_bam')
        uncollapsed_bam = get_most_recent_files_for_request(self.request_id, self.app, name='uncollapsed_bam')
        fgbio_group_reads_by_umi_bam = get_most_recent_files_for_request(self.request_id, self.app, name='fgbio_group_reads_by_umi_bam')

        # todo: need this?
        # indel_realignment_bam

        collapsed_bam = self.create_cwl_file_object(fgbio_collapsed_bam)
        duplex_bam = self.create_cwl_file_object(fgbio_filter_consensus_reads_duplex_bam)
        group_reads_by_umi_bam = self.create_cwl_file_object(fgbio_group_reads_by_umi_bam)
        simplex_bam = self.create_cwl_file_object(fgbio_postprocessing_simplex_bam)
        uncollapsed_bam_base_recal = self.create_cwl_file_object(uncollapsed_bam)

        sample_name = uncollapsed_bam.split('_cl_aln')[0]
        sample_group = sample_name.split('-')[0:2]
        sample_sex = 'unknown'
        samples_json_content = json.dumps('metadata')

        input_file = template.render(
            collapsed_bam=collapsed_bam,
            duplex_bam=duplex_bam,
            group_reads_by_umi_bam=group_reads_by_umi_bam,
            simplex_bam=simplex_bam,
            uncollapsed_bam_base_recal=uncollapsed_bam_base_recal,
            sample_group=sample_group,
            sample_name=sample_name,
            sample_sex=sample_sex,
            samples_json_content=samples_json_content,
        )

        sample_input = json.loads(input_file)
        return sample_input

    def create_cwl_file_object(self, file_path):
        return {
            "class": "File",
            "location": file_path
        }
