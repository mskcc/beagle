"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
from jinja2 import Template

from runner.models import Port
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File, FileRepository


# Todo: Change this ID in staging when running tests
ACCESS_CURATED_BAMS_FILE_GROUP = '1a1b29cf-3bc2-4f6c-b376-d4c5d70116aa'
ACCESS_DEFAULT_NORMAL_BAM_FILE_ID = '2f77f3ac-ab25-4a02-90bd-86542401ac82'
WORKDIR = os.path.dirname(os.path.abspath(__file__))
BAM_FILE_TYPE = 3 # todo: put in better location

class AccessLegacySNVOperator(Operator):

    # Will be populated after get_sample_inputs()
    sample_inputs = None
    number_of_inputs = None

    def get_sample_inputs(self):

        run_ids = self.run_ids

        tumor_bams = []
        patient_ids = []
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

                print(simplex_bam_port)

                simplex_bam = simplex_bam_port[i]

                if t_n_port[i] == 'Tumor':
                    patient_ids.append(patient_id)
                    tumor_bams.append(duplex_bam)
                    tumor_simplex_bams.append(simplex_bam)
                    sample_ids.append(sample_id)

                    matched_normal_bams = FileRepository.filter(
                        file_type='bam',
                        metadata={
                            'patientId': patient_id,
                            'tumorOrNormal': 'Normal',
                            'igocomplete': True
                        }
                    )

                    if not len(matched_normal_bams) > 0:
                        msg = 'No matching normals found for patient {}'.format(patient_id)
                        raise Exception(msg)

                    # Todo: instead of looking at the file name, how to query for Unfiltered Bam files only? use fileType: 'unfiltered_bam'?
                    unfiltered_matched_normals = [b for b in matched_normal_bams if b.file.file_name.endswith('__aln_srt_IR_FX.bam')]

                    if not len(unfiltered_matched_normals) > 0:
                        msg = 'No unfiltered normals found for patient {}'.format(patient_id)
                        raise Exception(msg)

                    # Todo: use the most recent normal
                    unfiltered_matched_normal = unfiltered_matched_normals[0]
                    matched_normals.append(unfiltered_matched_normal)
                    # Todo: will this work to get sample ID from file?
                    matched_normal_ids.append(unfiltered_matched_normal.metadata['sampleName'])

        sample_inputs = []
        for i, b in enumerate(tumor_bams):

            sample_input = self.construct_sample_inputs(
                patient_ids[i],
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

        :return:
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

    def get_curated_normals(self, patient_id):
        """
        Return curated normal bams as yaml file objects

        :return: (list, list)
        """
        curated_normal_bams = FileRepository.filter(
            metadata={
                'fileGroup': ACCESS_CURATED_BAMS_FILE_GROUP
            }
        )
        normal_bams = [{'class': 'File', 'location': b.path} for b in curated_normal_bams]

        # Todo: Should we add the ID suffix here or save it as metadata in the DB?
        # For now we are saving it as a metadata field "snv_pipeline_id"
        normal_ids = [n['metadata']['snv_pipeline_id'] for n in curated_normal_bams]

        return normal_bams, normal_ids

    def construct_sample_inputs(self, patient_id, tumor_bam, tumor_simplex_bam, tumor_sample_id, matched_normal_bam, normal_sample_id):
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": "juno://" + tumor_bam['path']
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

            curated_normal_bams, curated_normal_ids = self.get_curated_normals(patient_id=patient_id)
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
