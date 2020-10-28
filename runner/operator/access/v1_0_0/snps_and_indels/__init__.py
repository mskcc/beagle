"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
from jinja2 import Template

from runner.models import Port
from file_system.models import FileGroup, FileMetadata
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File, FileRepository


# Todo: Change this ID in staging when running tests
ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_BAM_FILE_ID = '2f77f3ac-ab25-4a02-90bd-86542401ac82'
WORKDIR = os.path.dirname(os.path.abspath(__file__))


class AccessLegacySNVOperator(Operator):

    # Will be populated after get_sample_inputs()
    sample_inputs = None
    number_of_inputs = None

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        run_ids = self.run_ids

        tumor_bams = []
        tumor_simplex_bams = []
        sample_ids = []
        matched_normals = []
        matched_normal_ids = []

        for run_id in run_ids:
            port_list = Port.objects.filter(run=run_id)

            duplex_bam_port = [p for p in port_list if p.name == 'duplex_bams'][0].value
            simplex_bam_port = [p for p in port_list if p.name == 'simplex_bams'][0].value
            patient_id_port = [p for p in port_list if p.name == 'patient_id'][0].value
            sample_id_port = [p for p in port_list if p.name == 'add_rg_ID'][0].value
            t_n_port = [p for p in port_list if p.name == 'sample_class'][0].value

            for i, duplex_bam in enumerate(duplex_bam_port):
                sample_id = sample_id_port[i]
                patient_id = patient_id_port[i]
                simplex_bam = simplex_bam_port[i]

                if t_n_port[i] == 'Tumor':
                    tumor_bams.append(duplex_bam)
                    tumor_simplex_bams.append(simplex_bam)
                    sample_ids.append(sample_id)

                    # Use the suffix for access unfiltered bams to get only those bams
                    unfiltered_matched_normal_bam = FileRepository.filter(
                        file_type='bam',
                        path_regex='__aln_srt_IR_FX.bam',
                        metadata={
                            'patientId': patient_id,
                            'tumorOrNormal': 'Normal',
                            'igocomplete': True
                        }
                    ).latest('created_date')

                    if not unfiltered_matched_normal_bam:
                        msg = 'No matching unfiltered normals Bam found for patient {}'.format(patient_id)
                        raise Exception(msg)

                    matched_normals.append(unfiltered_matched_normal_bam)
                    matched_normal_ids.append(unfiltered_matched_normal_bam.metadata['sampleName'])

        sample_inputs = []
        for i, b in enumerate(tumor_bams):

            sample_input = self.construct_sample_inputs(
                b,
                tumor_simplex_bams[i],
                sample_ids[i],
                matched_normals[i],
                matched_normal_ids[i]
            )
            sample_inputs.append(sample_input)

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
                        'name': "ACCESS LEGACY SNV M1: %s, %i of %i" % (self.request_id, i + 1, self.number_of_inputs),
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

    def get_curated_normals(self):
        """
        Return ACCESS curated normal bams as yaml file objects

        :return: (list, list)
        """
        curated_normals_metadata = FileMetadata.objects.filter(
            file__file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG
        )
        curated_normal_bams = [f.file for f in curated_normals_metadata]
        curated_normal_ids = [f.metadata['snv_pipeline_id'] for f in curated_normals_metadata]
        normal_bams = [{'class': 'File', 'location': b.path} for b in curated_normal_bams]
        return normal_bams, curated_normal_ids

    def construct_sample_inputs(self, tumor_bam, tumor_simplex_bam, tumor_sample_id, matched_normal_bam, normal_sample_id):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": tumor_bam['path']
            }]
            normal_sample_names = ['']
            matched_normal_ids = [normal_sample_id]

            # Todo: how to know which sequencer's default normal to use?
            normal_bam = File.objects.get(pk=ACCESS_DEFAULT_NORMAL_BAM_FILE_ID)
            normal_bams = [{
                "class": "File",
                "location": normal_bam.path
            }]

            genotyping_bams = [
                {
                    "class": "File",
                    "location": tumor_bam['path']
                },
                {
                    "class": "File",
                    "location": tumor_simplex_bam['path']
                },
                {
                    "class": "File",
                    "location": matched_normal_bam.file.path
                }
            ]
            genotyping_bams_ids = [tumor_sample_id, tumor_sample_id + '-SIMPLEX', normal_sample_id]
            curated_normal_bams, curated_normal_ids = self.get_curated_normals()
            genotyping_bams += curated_normal_bams
            genotyping_bams_ids += curated_normal_ids

            input_file = template.render(
                tumor_bams=json.dumps(tumor_bams),
                normal_bams=json.dumps(normal_bams),
                tumor_sample_names=json.dumps(tumor_sample_names),
                normal_sample_names=json.dumps(normal_sample_names),
                matched_normal_ids=json.dumps(matched_normal_ids),
                genotyping_bams=json.dumps(genotyping_bams),
                genotyping_bams_ids=json.dumps(genotyping_bams_ids),
            )

            sample_input = json.loads(input_file)
            return sample_input
