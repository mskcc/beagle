"""""""""""""""""""""""""""""
" ACCESS-Pipeline MSI workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/msi.cwl
"""""""""""""""""""""""""""""

import os
import json
from jinja2 import Template

from runner.operator.operator import Operator
from runner.models import Port, Run, RunStatus
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository

SAMPLE_ID_SEP = '_cl_aln'
TUMOR_SEARCH = '-L0'
NORMAL_SEARCH = '-N0'
WORKDIR = os.path.dirname(os.path.abspath(__file__))

class AccessLegacyMSIOperator(Operator):
    """
    Operator for the ACCESS Legacy Microsatellite Instability workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/msi.cwl

    This Operator will search for ACCESS Standard Bam files based on an IGO Request ID. It will
    also find the matched normals based on the patient ID.
    """

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator.

        :return: list of json_objects
        """
        # Get the latest completed runs for the given request ID
        group_id = Run.objects.filter(
            tags__requestId=self.request_id,
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
        standard_tumor_bam_files = [f for p in standard_bam_ports for f in p.value if TUMOR_SEARCH in f['path'].split('/')[-1]]
        sample_ids_to_run = [f['path'].split('/')[-1].split(SAMPLE_ID_SEP)[0] for f in standard_tumor_bam_files]

        sample_ids = []
        tumor_bams = []
        matched_normal_bams = []

        for i, tumor_sample_id in enumerate(sample_ids_to_run):
            # Find the Tumor Standard bam
            sample_regex = r'{}_cl_aln_srt_MD_IR_FX_BR.bam'.format(tumor_sample_id)
            tumor_bam = FileRepository.filter(file_name_regex=sample_regex)

            if not len(tumor_bam) == 1:
                msg = 'Found incorrect number of matching bam files ({}) for sample {}'
                msg = msg.format(len(tumor_bam), tumor_sample_id)
                raise Exception(msg)
                # Todo: if > 1, choose based on run ID

            tumor_bam = tumor_bam[0]
            patient_id = tumor_sample_id.split('-')[0:2]

            # Find the matched Normal Standard bam (which could be associated with a different request_id)
            sample_regex = r'{}.*{}.*_cl_aln_srt_MD_IR_FX_BR.bam'.format(patient_id, NORMAL_SEARCH)
            matched_normal_bam = FileRepository.filter(path_regex=sample_regex)

            if not len(matched_normal_bam) > 0:
                msg = 'No matching standard normal Bam found for patient {}'.format(patient_id)
                raise Exception(msg)

            matched_normal_bam = matched_normal_bam.order_by('-created_date').first()

            sample_ids.append(tumor_sample_id)
            tumor_bams.append(tumor_bam)
            matched_normal_bams.append(matched_normal_bam)

        sample_inputs = [self.construct_sample_inputs(
            sample_ids[i],
            tumor_bams[i],
            matched_normal_bams[i]
        ) for i in range(0, len(sample_ids))]

        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        inputs = self.get_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY MSI M1: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleIds': job["sample_name"]
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(inputs)
        ]

    def construct_sample_inputs(self, sample_name, tumor_bam, matched_normal_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

        sample_names = [sample_name]
        matched_normal_bams = [{
            "class": "File",
            "location": 'juno://' + matched_normal_bam.file.path
        }]

        tumor_bams = [{
            "class": "File",
            "location": 'juno://' + tumor_bam.file.path
        }]

        input_file = template.render(
            tumor_bams=json.dumps(tumor_bams),
            normal_bams=json.dumps(matched_normal_bams),
            sample_names=json.dumps(sample_names),
        )

        sample_input = json.loads(input_file)
        return sample_input
