"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import json
from jinja2 import Template

from runner.models import Port
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


def get_curated_normals():
    """
    Return curated normal bams as yaml file objects

    :return: (list, list)
    """
    normal_paths = open('runner/operator/access/v1_0_0/snps_and_indels/DMP_curated_bams.txt').read().split('\n')
    normal_ids = open('runner/operator/access/v1_0_0/snps_and_indels/DMP_curated_bam_ids.txt').read().split('\n')
    normal_files = [{"class": "File", "location": p} for p in normal_paths]
    return normal_files, normal_ids


def construct_sample_inputs(tumor_bam, tumor_simplex_bam, tumor_sample_id, matched_normal_bam, normal_sample_id):
    with open('runner/operator/access/v1_0_0/snps_and_indels/input_template.json.jinja2') as file:
        template = Template(file.read())

        tumor_sample_names = [tumor_sample_id]
        tumor_bams = [{
            "class": "File",
            "location": "juno://" + tumor_bam['path']
        }]

        normal_sample_names = ['']
        matched_normal_ids = [normal_sample_id]

        # Todo: how to know which sequencer's default normal to use?
        normal_bams = [{
            "class": "File",
            "location": "/ifs/work/bergerm1/ACCESS-Projects/hiseq_curated_duplex/F22_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
        }]

        genotyping_bams = [
            {
                "class": "File",
                "location": tumor_bam['metadata']['path']
            },
            {
                "class": "File",
                "location": tumor_simplex_bam['metadata']['path']
            },
            {
                "class": "File",
                "location": matched_normal_bam['metadata']['path']
            }
        ]
        genotyping_bams_ids = [tumor_sample_id, tumor_sample_id + '-SIMPLEX', normal_sample_id]

        curated_normal_bams, curated_normal_ids = get_curated_normals()
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


class AccessLegacySNVOperator(Operator):
    def get_jobs(self):

        run_ids = self.run_ids
        tumor_bams = []
        tumor_simplex_bams = []
        sample_ids = []
        matched_normals = []
        matched_normal_ids = []
        for run_id in run_ids:
            port_list = Port.objects.filter(run=run_id)

            # for b in port_list.bam_dirs:
            for i, b in enumerate(port_list.duplex_bams):
                print(b)

                sample_id = b['metadata']['cmoSampleId']
                patient_id = b['metadata']['patientId']

                # todo: brittle, need a new field for bam type (or use new FileType?)
                duplex_bam = b
                simplex_bam = port_list.simplex_bams[i]

                if duplex_bam[0]['metadata']['tumorOrNormal'] == 'Tumor':

                    tumor_bams.append(duplex_bam)
                    tumor_simplex_bams.append(simplex_bam)
                    sample_ids.append(sample_id)

                    matched_normal_bams = FileRepository.filter(
                        queryset=self.files,
                        metadata={
                            'patientId': patient_id,
                            'tumorOrNormal': 'Normal',
                            'igocomplete': True
                        }
                    )

                    if not len(matched_normal_bams) > 0:
                        msg = 'No matching normals found for patient {}'.format(patient_id)
                        raise Exception(msg)

                    unfiltered_matched_normals = [b for b in matched_normal_bams if b['file_name'].endswith('__aln_srt_IR_FX.bam')]

                    if not len(unfiltered_matched_normals) > 0:
                        msg = 'No unfiltered normals found for patient {}'.format(patient_id)
                        raise Exception(msg)

                    # Todo: use the most recent normal
                    unfiltered_matched_normal = unfiltered_matched_normals[0]
                    matched_normals.append(unfiltered_matched_normal)
                    matched_normal_ids.append(unfiltered_matched_normal['metadata']['cmoSampleId'])

        sample_inputs = []
        for i, b in enumerate(tumor_bams):

            sample_input = construct_sample_inputs(
                b,
                tumor_simplex_bams[i],
                sample_ids[i],
                matched_normals[i],
                matched_normal_ids[i]
            )

            sample_inputs.append(sample_input)

        number_of_inputs = len(sample_inputs)

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY SNV M1: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs),
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

            for i, job in enumerate(sample_inputs)
        ]
