"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
import logging
from jinja2 import Template

from runner.models import Port, Run, RunStatus
from file_system.models import FileMetadata
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import File, FileRepository


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam$'
NORMAL_SAMPLE_SEARCH = '-N0'

class AccessLegacySNVOperator(Operator):

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

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

        # Get all duplex bam ports for these runs
        access_duplex_output_ports = Port.objects.filter(
            name='duplex_bams',
            run__id__in=[r.id for r in request_id_runs],
            run__status=RunStatus.COMPLETED
        )
        # Each port is a list, so need a double list comprehension here
        all_access_output_records = [f for p in access_duplex_output_ports for f in p.value]
        # these are port objects, they dont have metadata field
        tumors_to_run = [r['sampleId'] for r in all_access_output_records if r['tumorOrNormal'] == 'Tumor']

        sample_ids = []
        tumor_duplex_bams = []
        tumor_simplex_bams = []
        matched_normals = []
        matched_normal_ids = []

        for i, tumor_sample_id in enumerate(tumors_to_run):

            # Locate the Duplex BAM
            sample_regex = r'{}.*__aln_srt_IR_FX-duplex.bam$'.format(tumor_sample_id)

            tumor_duplex_bam = FileRepository.filter(path_regex=sample_regex)
            if len(tumor_duplex_bam) < 1:
                msg = 'ERROR: Could not find matching duplex bam file for sample {}'
                msg = msg.format(tumor_sample_id)
                logger.exception(msg)
                raise Exception(msg)
            if len(tumor_duplex_bam) > 1:
                msg = 'WARNING: Found more than one matching duplex bam file for sample {}. \
                We will choose the most recently-created one for this run.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
            # Take the latest one
            tumor_duplex_bam = tumor_duplex_bam.order_by('-created_date').first()

            # Locate the Simplex BAM
            sample_regex = r'{}.*__aln_srt_IR_FX-simplex.bam$'.format(tumor_sample_id)
            tumor_simplex_bam = FileRepository.filter(path_regex=sample_regex)
            if len(tumor_simplex_bam) < 1:
                msg = 'ERROR: Could not find matching simplex bam file for sample {}'
                msg = msg.format(tumor_sample_id)
                logger.exception(msg)
                raise Exception(msg)
            if len(tumor_simplex_bam) > 1:
                msg = 'WARNING: Found more than one matching simplex bam file for sample {}. ' \
                      'We will choose the most recently-created one for this run.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
            # Take the latest one
            tumor_simplex_bam = tumor_simplex_bam.order_by('-created_date').first()

            patient_id = tumor_sample_id.split('-')[0:2]

            # Locate the Matched, Unfiltered, Normal BAM
            sample_regex = r'{}.*{}.*__aln_srt_IR_FX.bam$'.format(patient_id, NORMAL_SAMPLE_SEARCH)
            unfiltered_matched_normal_bam = FileRepository.filter(path_regex=sample_regex)
            if len(unfiltered_matched_normal_bam) < 1:
                msg = 'WARNING: Could not find matching unfiltered normal bam file for sample {}' \
                      'We will skip running this sample.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
                raise Exception(msg)
            if len(unfiltered_matched_normal_bam) > 1:
                msg = 'WARNING: Found more than one matching unfiltered normal bam file for tumor sample {}. ' \
                      'We will choose the most recently-created one for this run.'
                msg = msg.format(tumor_sample_id)
                logger.warning(msg)
            # Take the latest one
            unfiltered_matched_normal_bam = unfiltered_matched_normal_bam.order_by('-created_date').first()

            # Parse the Normal Sample ID from the file name
            # Todo: Stop using file path for this, once output_metadata is being supplied in access legacy operator
            unfiltered_matched_normal_file_base = unfiltered_matched_normal_bam.file.path.split('/')[-1]
            unfiltered_matched_normal_sample_id = '-'.join(unfiltered_matched_normal_file_base.split('-')[0:3])

            sample_ids.append(tumor_sample_id)
            tumor_duplex_bams.append(tumor_duplex_bam)
            tumor_simplex_bams.append(tumor_simplex_bam)
            matched_normals.append(unfiltered_matched_normal_bam)
            matched_normal_ids.append(unfiltered_matched_normal_sample_id)

        sample_inputs = []
        for i, b in enumerate(tumor_duplex_bams):

            sample_input = self.construct_sample_inputs(
                b,
                tumor_simplex_bams[i],
                sample_ids[i],
                matched_normals[i],
                matched_normal_ids[i]
            )
            sample_inputs.append(sample_input)
        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        sample_inputs = self.get_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY SNV M1: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
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
        normal_bams = [
            {
                'class': 'File',
                'location': 'juno://' + b.path
            } for b in curated_normal_bams
        ]
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
                "location": 'juno://' + tumor_bam.file.path
            }]
            matched_normal_ids = [normal_sample_id]

            # Todo: how to know which sequencer's default normal to use?
            normal_bam = FileRepository.filter(
                file_type='bam',
                path_regex=ACCESS_DEFAULT_NORMAL_FILENAME
            )[0].file
            normal_bams = [{
                "class": "File",
                "location": 'juno://' + normal_bam.path
            }]
            normal_sample_names = [ACCESS_DEFAULT_NORMAL_ID]

            genotyping_bams = [
                {
                    "class": "File",
                    "location": 'juno://' + tumor_bam.file.path
                },
                {
                    "class": "File",
                    "location": 'juno://' + tumor_simplex_bam.file.path
                },
                {
                    "class": "File",
                    "location": 'juno://' + matched_normal_bam.file.path
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
