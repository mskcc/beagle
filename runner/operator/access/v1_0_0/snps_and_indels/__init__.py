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


def construct_sample_inputs(tumor_bam, sample_id, matched_normal_bam, normal_sample_id):
    with open('runner/operator/access/v1_0_0/snps_and_indels/input_template.json.jinja2') as file:
        template = Template(file.read())

        tumor_sample_names = [sample_id]
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

        genotyping_bams = [{
            "class": "File",
            "location": matched_normal_bam['metadata']['path']
        }]
        genotyping_bams_ids = [normal_sample_id]

        # todo:
        genotyping_bams += get_curated_normals()
        genotyping_bams_ids += get_curated_normal_ids()

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
        sample_ids = []
        matched_normals = []
        matched_normal_ids = []
        for run_id in run_ids:
            port_list = Port.objects.filter(run=run_id)

            # for b in port_list.bam_dirs:
            for b in port_list.bam_dirs:

                # todo: this is brittle
                sample_id = b['metadata']['path'].split('/')[-1].split('__')[0]

                # todo: possible to also get patient ID here?
                patient_id = b['metadata']['path'].split('/')[-1].split('__')[0].split('-')[0, 2]
                patient_id = '-'.join(patient_id)

                # Use port to query for metadata for these output files
                files = FileRepository.filter(
                    queryset=self.files,
                    metadata={
                        'cmoSampleId': sample_id,
                        'igocomplete': True
                    }
                )

                assert len(files) == 1, 'Found incorrect matching file found for sample {}'.format(sample_id)

                if files[0]['metadata']['tumorOrNormal'] == 'Tumor':

                    # Todo: include logic for choosing most recent / highest coverage Normal here
                    matched_normal = FileRepository.filter(
                        queryset=self.files,
                        metadata={
                            'patientId': patient_id,
                            'tumorOrNormal': 'Normal',
                            'igocomplete': True
                        }
                    )

                    tumor_bams.append(get_file_obj(files[0]))
                    sample_ids.append(sample_id)
                    matched_normals.append(matched_normal)
                    matched_normal_ids.append(matched_normal['metadata']['cmoSampleId'])

        tumor_bams = [
            {
                "id": f.file.id,
                "path": f.file.path,
                "file_name": f.file.file_name,
                "metadata": f.metadata
            } for f in files
        ]
 
        sample_inputs = []
        for i, b in enumerate(tumor_bams):

            (sample_input, no_of_errors) = construct_sample_inputs(
                b,
                sample_ids[i],
                matched_normals[i],
                matched_normal_ids[i]
            )

            if no_of_errors:
                return
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
