"""""""""""""""""""""""""""""
" ACCESS-Pipeline SNV workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/snps_and_indels.cwl
"""""""""""""""""""""""""""""

import os
import json
import logging
from jinja2 import Template
from django.db.models import Q

from file_system.models import File
from runner.models import Port, RunStatus
from file_system.models import FileMetadata
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository
from runner.operator.access import get_request_id_runs, get_unfiltered_matched_normal


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam'
NORMAL_SAMPLE_SEARCH = '-N0'
TUMOR_SAMPLE_SEARCH = '-L0'
DUPLEX_BAM_SEARCH = '__aln_srt_IR_FX-duplex.bam'
SIMPLEX_BAM_SEARCH = '__aln_srt_IR_FX-simplex.bam'
DMP_DUPLEX_REGEX = '-duplex.bam'
DMP_SIMPLEX_REGEX = '-simplex.bam'


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
        #
        # Todo: Does this fail in the following case?
        # C-000884-L001-d_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam
        # C-000884-L0011-d_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam
        #
        # What if the -d isn't present? Will sample IDs always have these terminators?
        tumor_duplex_bam = File.objects.filter(file_name__startswith=tumor_sample_id, file_name__endswith=DUPLEX_BAM_SEARCH)
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
        tumor_simplex_bam = File.objects.filter(file_name__startswith=tumor_sample_id, file_name__endswith=SIMPLEX_BAM_SEARCH)
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

        (capture_samples_duplex,
         capture_samples_simplex,
         capture_samples_duplex_sample_ids,
         capture_samples_simplex_sample_ids) = self.get_pool_genotyping_samples(tumor_sample_id)

        sample_info = {
            'tumor_sample_id': tumor_sample_id,
            'tumor_duplex_bam': tumor_duplex_bam,
            'tumor_simplex_bam': tumor_simplex_bam,
            'matched_normal_unfiltered': matched_normal_unfiltered_bam,
            'matched_normal_unfiltered_id': matched_normal_unfiltered_id,
            'capture_samples_duplex': capture_samples_duplex,
            'capture_samples_simplex': capture_samples_simplex,
            'capture_samples_duplex_sample_ids': capture_samples_duplex_sample_ids,
            'capture_samples_simplex_sample_ids': capture_samples_simplex_sample_ids
        }

        return sample_info

    def get_pool_genotyping_samples(self, tumor_sample_id):
        """
        Use the initial fastq metadata to get the capture of the sample,
        then, based on this capture ID, find tumor and matched normal simplex and duplex bams for genotyping

        Limits to 40 samples (or 80 bams, because each has Simplex and Duplex)

        Todo: put metadata on the Bams themselves

        :param tumor_sample_id: str
        :return:
        """
        capture_id = FileRepository.filter(
            file_type='fastq',
            metadata={'sampleName': tumor_sample_id}
        )[0].metadata['captureName']

        sample_id_fastqs = FileRepository.filter(
            file_type='fastq',
            metadata={'captureName': capture_id}
        )
        sample_ids = list(set([f.metadata['sampleName'] for f in sample_id_fastqs]))

        tumor_capture_sample_ids = [i for i in sample_ids if TUMOR_SAMPLE_SEARCH in i]
        normal_capture_sample_ids = [i for i in sample_ids if NORMAL_SAMPLE_SEARCH in i]

        tumor_capture_q = Q(
            *[('file_name__startswith', id) for id in tumor_capture_sample_ids],
            _connector=Q.OR
        )

        normal_capture_q = Q(
            *[('file_name__startswith', id) for id in normal_capture_sample_ids],
            _connector=Q.OR
        )

        q = tumor_capture_q & Q(path__endswith=DUPLEX_BAM_SEARCH)
        capture_samples_duplex = File.objects.filter(q)
        sids = [s.file_name.split('_cl_aln_srt')[0] for s in capture_samples_duplex]

        for sid in sids:
            patient_id = '-'.join(sid.split('-')[0:2])

            q = normal_capture_q & \
                Q(file_name__startswith=patient_id + NORMAL_SAMPLE_SEARCH) & \
                Q(file_name__endswith=DUPLEX_BAM_SEARCH)

            normal_capture_sample_duplex = File.objects.filter(q)

            if len(normal_capture_sample_duplex) > 0:
                capture_samples_duplex |= normal_capture_sample_duplex.order_by('-created_date')[:1]

        q = tumor_capture_q & Q(path__endswith=SIMPLEX_BAM_SEARCH)
        capture_samples_simplex = File.objects.filter(q)
        sids = [s.file_name.split('_cl_aln_srt')[0] for s in capture_samples_simplex]

        for sid in sids:
            patient_id = '-'.join(sid.split('-')[0:2])

            q = normal_capture_q & \
                Q(file_name__startswith=patient_id + NORMAL_SAMPLE_SEARCH) & \
                Q(file_name__endswith=SIMPLEX_BAM_SEARCH)

            normal_capture_sample_simplex = File.objects.filter(q)

            if len(normal_capture_sample_simplex) > 0:
                capture_samples_simplex |= normal_capture_sample_simplex.order_by('-created_date')[:1]

        # Limit to 40 samples, and sort by patient ID to ensure each of T and N matching samples are found
        capture_samples_duplex = sorted(capture_samples_duplex, key=lambda s: s.file_name)[0:40]
        capture_samples_simplex = sorted(capture_samples_simplex, key=lambda s: s.file_name)[0:40]

        capture_samples_duplex_sample_ids = [s.path.split('_cl_aln_srt')[0] for s in capture_samples_duplex]
        capture_samples_simplex_sample_ids = [s.path.split('_cl_aln_srt')[0] for s in capture_samples_simplex]

        return capture_samples_duplex, capture_samples_simplex, capture_samples_duplex_sample_ids, capture_samples_simplex_sample_ids

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
                            'cmoSampleIds': job["tumor_sample_names"],
                            'patientId': '-'.join(job["tumor_sample_names"][0].split('-')[0:2])
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
        curated_normal_bams = [f for f in curated_normals_metadata]
        curated_normal_ids = [f.metadata['snv_pipeline_id'] for f in curated_normals_metadata]
        normal_bams = [
            {
                'class': 'File',
                'location': 'juno://' + b.file.path
            } for b in curated_normal_bams
        ]
        return normal_bams, curated_normal_ids

    def construct_sample_inputs(self, tumor_sample_id, tumor_duplex_bam, tumor_simplex_bam, matched_normal_unfiltered,
                                matched_normal_unfiltered_id, capture_samples_duplex,
                                capture_samples_simplex, capture_samples_duplex_sample_ids, capture_samples_simplex_sample_ids):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

            tumor_sample_names = [tumor_sample_id]
            tumor_bams = [{
                "class": "File",
                "location": 'juno://' + tumor_duplex_bam.path
            }]
            matched_normal_ids = [matched_normal_unfiltered_id]

            # Todo: how to know which sequencer's default normal to use?
            normal_bam = File.objects.filter(
                file_type__name='bam',
                file_name=ACCESS_DEFAULT_NORMAL_FILENAME
            )[0]
            normal_bams = [{
                "class": "File",
                "location": 'juno://' + normal_bam.path
            }]
            normal_sample_names = [ACCESS_DEFAULT_NORMAL_ID]

            genotyping_bams = [
                {
                    "class": "File",
                    "location": 'juno://' + tumor_duplex_bam.path
                },
                {
                    "class": "File",
                    "location": 'juno://' + tumor_simplex_bam.path
                }
            ]

            genotyping_bams_ids = [tumor_sample_id, tumor_sample_id + '-SIMPLEX']

            # Matched Normal may or may not be available for genotyping
            if matched_normal_unfiltered:
                genotyping_bams += [{
                    "class": "File",
                    "location": 'juno://' + matched_normal_unfiltered.path
                }]
                genotyping_bams_ids += [matched_normal_unfiltered_id]

            # Additional matched Tumors may be available
            if len(capture_samples_duplex) > 0:
                genotyping_bams += [
                    {
                        "class": "File",
                        "location": 'juno://' + b.path
                    } for b in capture_samples_duplex
                ]
                genotyping_bams_ids += capture_samples_duplex_sample_ids

                genotyping_bams += [
                    {
                        "class": "File",
                        "location": 'juno://' + b.path
                    } for b in capture_samples_simplex
                ]
                genotyping_bams_ids += [i + '-SIMPLEX' for i in capture_samples_simplex_sample_ids]

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
