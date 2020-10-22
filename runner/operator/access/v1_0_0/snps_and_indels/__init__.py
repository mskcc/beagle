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
from file_system.repository.file_repository import FileRepository



# Todo: create FileGroup for access curated bams and use ID here
ACCESS_CURATED_BAMS_FILE_GROUP = ''
WORKDIR = os.path.dirname(os.path.abspath(__file__))


def get_curated_normals(patient_id):
    """
    Return curated normal bams as yaml file objects

    :return: (list, list)
    """
    normal_bams = FileRepository.filter(
        metadata={
            'patientId': patient_id,
            'tumorOrNormal': 'Normal',
            'igocomplete': True,
            'fileGroup': ACCESS_CURATED_BAMS_FILE_GROUP
        }
    )
    normal_bams = [{'class': 'File', 'location': b.path} for b in normal_bams]
    normal_ids = [n['metadata']['cmoSampleId'] for n in normal_bams]
    return normal_bams, normal_ids


def construct_sample_inputs(patient_id, tumor_bam, tumor_simplex_bam, tumor_sample_id, matched_normal_bam, normal_sample_id):
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

        curated_normal_bams, curated_normal_ids = get_curated_normals(patient_id=patient_id)
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
        patient_ids = []
        tumor_simplex_bams = []
        sample_ids = []
        matched_normals = []
        matched_normal_ids = []
        for run_id in run_ids:
            port_list = Port.objects.filter(run=run_id)
            for port in port_list:
                if port.name == 'duplex_bams':

                    print(port)
                    print(port.value)
                    print(port.files)
                    print(dir(port))

                    for i, b in enumerate(port.files):
                        print(b)

                        sample_id = b['metadata']['cmoSampleId']
                        patient_id = b['metadata']['patientId']
                        patient_ids.append(patient_id)

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
                patient_ids[i],
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
