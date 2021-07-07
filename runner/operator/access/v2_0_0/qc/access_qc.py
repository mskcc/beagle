import os
import json
import logging

from jinja2 import Template

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer

from runner.models import RunStatus, Port, OperatorRun



logger = logging.getLogger(__name__)
WORKDIR = os.path.dirname(os.path.abspath(__file__))


meta_fields = [
    'igoId',
    'cmoSampleName',
    'sampleName',
    'cmoSampleClass',
    'cmoPatientId',
    'investigatorSampleId',
    'oncoTreeCode',
    'tumorOrNormal',
    'tissueLocation',
    'specimenType',
    'sampleOrigin',
    'preservation',
    'collectionYear',
    'sex',
    'species',
    'tubeId',
    'cfDNA2dBarcode',
    'baitSet',
    'qcReports',
    'barcodeId',
    'barcodeIndex',
    'libraryIgoId',
    'libraryVolume',
    'libraryConcentrationNgul',
    'dnaInputNg',
    'captureConcentrationNm',
    'captureInputNg',
    'captureName'
]

class AccessQCOperator(Operator):
    """
    Operator for the ACCESS QC workflow:

    https://github.com/msk-access/access_qc_generation/blob/master/access_qc.cwl

    This Operator will search for Nucleo Bam files based on an IGO Request ID
    """
    def get_jobs(self):

        sample_inputs = self.get_nucleo_outputs()

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

    def parse_nucleo_output_ports(self, run, port_name):
        bam = Port.objects.filter(
            name=port_name,
            run__id=run.pk
        )
        if not len(bam.files) == 1:
            raise Exception('Output port {} for run {} should have just one file'.format(port_name, run.id))

        bam = bam.files[0]
        bam = self.create_cwl_file_object(bam)
        return bam

    def construct_sample_inputs(self, run):
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

        port_names = [
            'duplex_bam',
            'simplex_bam',
            'collapsed_bam',
            'group_reads_by_umi_bam',
            'uncollapsed_bam_base_recal'
        ]

        bams = {}
        for n in port_names:
            bam = self.parse_nucleo_output_ports(run, n)
            bams[n] = bam

        sample_sex = 'unknown'
        sample_name = bams['uncollapsed_bam'].split('_cl_aln')[0]
        sample_group = sample_name.split('-')[0:2]
        samples_json_content = self.create_sample_json(run)

        input_file = template.render(
            **bams,
            sample_sex=sample_sex,
            sample_name=sample_name,
            sample_group=sample_group,
            samples_json_content=samples_json_content,
        )

        sample_input = json.loads(input_file)
        return sample_input

    def create_cwl_file_object(self, file_path):
        return {
            "class": "File",
            "location": file_path
        }

    @staticmethod
    def create_sample_json(run):
        j = run.output_metadata
        for f in meta_fields:
            if not f in j:
                j[f] = None
        return j

    def get_nucleo_outputs(self):
        most_recent_operator_run = OperatorRun.objects.filter(
            app='access nucleo',
            tags__requestId=self.request_id,
            status=RunStatus.COMPLETED
        ).order_by('-created_date').first()

        runs = most_recent_operator_run.runs
        if not len(runs):
            raise Exception('No matching Nucleo runs found for request {}'.format(self.request_id))

        inputs = []
        for r in runs:
            inp = self.construct_sample_inputs(r)
            inputs.append(inp)

        return inputs
