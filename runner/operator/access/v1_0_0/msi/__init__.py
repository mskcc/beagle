"""""""""""""""""""""""""""""
" ACCESS-Pipeline MSI workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/msi.cwl
"""""""""""""""""""""""""""""

import os
import json
from jinja2 import Template

from runner.models import Port, Run, RunStatus
from file_system.models import FileMetadata
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File, FileRepository


WORKDIR = os.path.dirname(os.path.abspath(__file__))

class AccessLegacyMSIOperator(Operator):

    # Will be populated after get_sample_inputs()
    sample_inputs = None
    number_of_inputs = None

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
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

        sample_ids = []
        tumor_bams = []
        matched_normal_bams = []

        for i, tumor_sample_id in enumerate(tumors_to_run):
            tumor_bam = FileRepository.filter(
                file_type='bam',
                path_regex='__cl_aln_srt_MD_IR_FX_BR.bam',
                metadata={
                    'tumorOrNormal': 'Tumor',
                    'sampleName': tumor_sample_id
                }
            )
            if not len(tumor_bams) == 1:
                msg = 'Found incorrect number of matching bam files ({}) for sample {}'
                msg = msg.format(len(tumor_duplex_bam), tumor_sample_id)
                raise Exception(msg)

            patient_id = tumor_bams.metadata['patientId']

            matched_normal_bam = FileRepository.filter(
                file_type='bam',
                path_regex='__cl_aln_srt_MD_IR_FX_BR.bam',
                metadata={
                    'tumorOrNormal': 'Normal',
                    'patientId': patient_id,
                }
            ).latest('created_date')

            if not matched_normal_bams:
                msg = 'No matching unfiltered normals Bam found for patient {}'.format(patient_id)
                raise Exception(msg)

            sample_ids.append(tumor_sample_id)
            tumor_bam.append(tumor_bam)
            matched_normal_bam.append(matched_normal_bam)

        sample_inputs = [self.construct_sample_inputs(
            sample_ids[i],
            tumor_bams[i],
            matched_normal_bams[i]
        ) for i in range(0, len(sample_ids))

        self.number_of_inputs = len(sample_inputs)
        self.sample_inputs = sample_inputs
        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY MSI M1: %s, %i of %i" % (self.request_id, i + 1, self.number_of_inputs),
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
            for i, job in enumerate(self.sample_inputs)
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
            "location": matched_normal_bam.file.path
        }]

        tumor_bams = [{
            "class": "File",
            "location": tumor_bam.file.path
        }]

        input_file = template.render(
            tumor_bams=json.dumps(tumor_bams),
            matched_normal_bams=json.dumps(normal_bams),
            sample_names=json.dumps(sample_names),
        )

        sample_input = json.loads(input_file)
        return sample_input
