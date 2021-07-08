import os
import json
import logging

from jinja2 import Template

from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer

from runner.models import RunStatus, Port, Run



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
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleId': job['sample_name']
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(sample_inputs)
        ]

    def get_nucleo_outputs(self):
        # Use most recent set of runs that completed successfully
        most_recent_runs_for_request = Run.objects.filter(
            app__name='access nucleo',
            tags__requestId=self.request_id,
            status=RunStatus.COMPLETED,
            operator_run__status=RunStatus.COMPLETED
        ).order_by('-created_date').first().operator_run.runs.all()

        if not len(most_recent_runs_for_request):
            raise Exception('No matching Nucleo runs found for request {}'.format(self.request_id))

        inputs = []
        for r in most_recent_runs_for_request:
            inp = self.construct_sample_inputs(r)
            inputs.append(inp)
        return inputs

    def parse_nucleo_output_ports(self, run, port_name):
        bam_bai = Port.objects.get(name=port_name, run=run.pk)
        if not len(bam_bai.files.all()) in [1, 2]:
            raise Exception('Port {} for run {} should have just 1 bam or 1 (bam/bai) pair'.format(port_name, run.id))

        bam = [b for b in bam_bai.files.all() if b.file_name.endswith('.bam')][0]
        bai = [b for b in bam_bai.files.all() if b.file_name.endswith('.bai')]
        bam = self.create_cwl_file_object(bam.path)
        if len(bai):
            bam['secondaryFiles'] = [{
                "class": "File",
                "path": bai[0].path
            }]
        return bam

    def construct_sample_inputs(self, run):
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

        nucleo_output_port_names = [
            'uncollapsed_bam',
            'fgbio_group_reads_by_umi_bam',
            'fgbio_collapsed_bam',
            'fgbio_filter_consensus_reads_duplex_bam',
            'fgbio_postprocessing_simplex_bam',
        ]
        qc_input_port_names = [
            'uncollapsed_bam_base_recal',
            'group_reads_by_umi_bam',
            'collapsed_bam',
            'duplex_bam',
            'simplex_bam',
        ]
        bams = {}
        for o, i in zip(nucleo_output_port_names, qc_input_port_names):
            # We are running a multi-sample workflow on just one sample,
            # so we create single-element lists here
            bam = [self.parse_nucleo_output_ports(run, o)]
            bams[i] = json.dumps(bam)

        sample_sex = 'unknown'
        sample_name = run.output_metadata['sampleName']
        sample_group = '-'.join(sample_name.split('-')[0:2])
        samples_json_content = self.create_sample_json(run)

        input_file = template.render(
            sample_sex=json.dumps([sample_sex]),
            sample_name=json.dumps([sample_name]),
            sample_group=json.dumps([sample_group]),
            samples_json_content=samples_json_content,
            **bams,
        )
        sample_input = json.loads(input_file)
        return sample_input

    def create_cwl_file_object(self, file_path):
        return {
            "class": "File",
            "location": "juno://" + file_path
        }

    @staticmethod
    def create_sample_json(run):
        j = run.output_metadata
        for f in meta_fields:
            if not f in j:
                j[f] = None
        return json.dumps(str(j))
