"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
import logging
from jinja2 import Template

from runner.models import Port, RunStatus
from file_system.models import FileMetadata
from runner.operator.operator import Operator
from runner.operator.access import get_request_id_runs, get_unfiltered_matched_normal
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam$'
NORMAL_SAMPLE_SEARCH = '-N0'
TUMOR_SAMPLE_SEARCH = '-L0'
DUPLEX_BAM_REGEX = r'{}.*__aln_srt_IR_FX-duplex.bam$'
SIMPLEX_BAM_REGEX = r'{}.*__aln_srt_IR_FX-simplex.bam$'


class AccessLegacySNVOperator(Operator):

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        if self.request_id:
            run_ids = get_request_id_runs(self.request_id)
            run_ids = [r.id for r in run_ids]
        else:
            run_ids = self.run_ids

        # Get all duplex bam ports for these runs
        access_duplex_output_ports = Port.objects.filter(
            name='duplex_bams',
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )
        # Each port is a list, so need a double list comprehension here
        all_access_output_records = [f for p in access_duplex_output_ports for f in p.value]
        # These are port objects, they don't have a metadata field
        tumors_to_run = [r['sampleId'] for r in all_access_output_records if r['tumorOrNormal'] == 'Tumor']

        # Gather input Files / Metadata
        sample_infos = []
        for tumor_sample_id in tumors_to_run:
            sample_info = self.create_sample_info(tumor_sample_id)
            sample_infos.append(sample_info)

        # Format input templates
        sample_inputs = []
        for sample_info in sample_infos:
            sample_input = self.construct_sample_inputs(**sample_info)
            sample_inputs.append(sample_input)

        return sample_inputs

    def create_sample_info(self, tumor_sample_id):
        """
        Query DB for all relevant files / metadata necessary for SNV pipeline input:

        - Tumor Duplex Bam
        - Tumor Simplex Bam
        - Matched Normal Unfiltered bam (from IGO / DMP or None) (external code)
        - Other Tumor Duplex bams from same patient (for genotyping)
        - Other Tumor Simplex bams from same patient (for genotyping)

        :return:
        """
        # Locate the most recent Duplex BAM
        sample_regex = DUPLEX_BAM_REGEX.format(tumor_sample_id)
        tumor_duplex_bam = FileRepository.filter(path_regex=sample_regex)
        if len(tumor_duplex_bam) < 1:
            msg = 'ERROR: Could not find matching duplex bam file for sample {}'
            msg = msg.format(tumor_sample_id)
            logger.exception(msg)
            raise Exception(msg)
        elif len(tumor_duplex_bam) > 1:
            msg = 'WARNING: Found more than one matching duplex bam file for sample {}. ' \
                  'We will choose the most recently-created one for this run.'
            msg = msg.format(tumor_sample_id)
            logger.warning(msg)
        tumor_duplex_bam = tumor_duplex_bam.order_by('-created_date').first()

        # Locate the most recent Simplex BAM
        sample_regex = SIMPLEX_BAM_REGEX.format(tumor_sample_id)
        tumor_simplex_bam = FileRepository.filter(path_regex=sample_regex)
        if len(tumor_simplex_bam) < 1:
            msg = 'ERROR: Could not find matching simplex bam file for sample {}'
            msg = msg.format(tumor_sample_id)
            logger.exception(msg)
            raise Exception(msg)
        elif len(tumor_simplex_bam) > 1:
            msg = 'WARNING: Found more than one matching simplex bam file for sample {}. ' \
                  'We will choose the most recently-created one for this run.'
            msg = msg.format(tumor_sample_id)
            logger.warning(msg)
        tumor_simplex_bam = tumor_simplex_bam.order_by('-created_date').first()

        patient_id = '-'.join(tumor_sample_id.split('-')[0:2])

        # Locate the Matched, Unfiltered, Normal BAM
        matched_normal_unfiltered_bam, matched_normal_unfiltered_id = get_unfiltered_matched_normal(patient_id)

        # Locate any Matched Tumor bams for genotyping
        matched_duplex_tumor_regex = DUPLEX_BAM_REGEX.format(patient_id + TUMOR_SAMPLE_SEARCH)
        matched_simplex_tumor_regex = SIMPLEX_BAM_REGEX.format(patient_id + TUMOR_SAMPLE_SEARCH)
        matched_duplex_tumors = FileRepository.filter(path_regex=matched_duplex_tumor_regex)
        matched_simplex_tumors = FileRepository.filter(path_regex=matched_simplex_tumor_regex)
        # Remove the main tumor being run
        matched_duplex_tumors = matched_duplex_tumors.exclude(file__file_name=tumor_duplex_bam.file.file_name)
        matched_simplex_tumors = matched_simplex_tumors.exclude(file__file_name=tumor_simplex_bam.file.file_name)
        matched_duplex_sample_ids = ['-'.join(b.file.path.split('/')[-1].split('-')[0:3]) for b in
                                     matched_duplex_tumors]
        matched_simplex_sample_ids = ['-'.join(b.file.path.split('/')[-1].split('-')[0:3]) for b in
                                      matched_simplex_tumors]

        sample_info = {
            'tumor_sample_id': tumor_sample_id,
            'tumor_duplex_bam': tumor_duplex_bam,
            'tumor_simplex_bam': tumor_simplex_bam,
            'matched_normal_unfiltered': matched_normal_unfiltered_bam,
            'matched_normal_unfiltered_id': matched_normal_unfiltered_id,
            'matched_tumors_duplex': matched_duplex_tumors,
            'matched_tumors_simplex': matched_simplex_tumors,
            'matched_tumors_duplex_sample_ids': matched_duplex_sample_ids,
            'matched_tumors_simplex_sample_ids': matched_simplex_sample_ids
        }

        return sample_info

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

    def construct_sample_inputs(self, tumor_sample_id, tumor_duplex_bam, tumor_simplex_bam, matched_normal_unfiltered,
                                matched_normal_unfiltered_id, matched_tumors_duplex, matched_tumors_simplex,
                                matched_tumors_duplex_sample_ids, matched_tumors_simplex_sample_ids):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": 'juno://' + tumor_duplex_bam.file.path
            }]
            matched_normal_ids = [matched_normal_unfiltered_id]

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
                    "location": 'juno://' + tumor_duplex_bam.file.path
                },
                {
                    "class": "File",
                    "location": 'juno://' + tumor_simplex_bam.file.path
                }
            ]

            genotyping_bams_ids = [tumor_sample_id, tumor_sample_id + '-SIMPLEX']

            # Matched Normal may or may not be available for genotyping
            if matched_normal_unfiltered:
                genotyping_bams += [{
                    "class": "File",
                    "location": 'juno://' + matched_normal_unfiltered.file.path
                }]
                genotyping_bams_ids += [matched_normal_unfiltered_id]

            # Additional matched Tumors may be available
            if len(matched_tumors_duplex) > 0:
                genotyping_bams += [
                    {
                        "class": "File",
                        "location": 'juno://' + b.file.path
                    } for b in matched_tumors_duplex
                ]
                genotyping_bams_ids += matched_tumors_duplex_sample_ids

                genotyping_bams += [
                    {
                        "class": "File",
                        "location": 'juno://' + b.file.path
                    } for b in matched_tumors_simplex
                ]
                genotyping_bams_ids += [i + '-SIMPLEX' for i in matched_tumors_simplex_sample_ids]

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
