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
from runner.operator.access import get_request_id_runs, get_unfiltered_matched_normal, get_request_id


logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))

ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = 'access_curated_normals'
ACCESS_DEFAULT_NORMAL_ID = 'DONOR22-TP'
ACCESS_DEFAULT_NORMAL_FILENAME = 'DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam'
NORMAL_SAMPLE_SEARCH = '-N0'
TUMOR_SAMPLE_SEARCH = '-L0'
DUPLEX_BAM_SEARCH = '__aln_srt_IR_FX-duplex.bam'
SIMPLEX_BAM_SEARCH = '__aln_srt_IR_FX-simplex.bam'
UNFILTERED_BAM_SEARCH = '__aln_srt_IR_FX.bam'
DMP_DUPLEX_REGEX = '-duplex.bam'
DMP_SIMPLEX_REGEX = '-simplex.bam'


class AccessLegacySNVOperator(Operator):

    fillout_duplex_tumors = None
    fillout_simplex_tumors = None
    fillout_unfiltered_normals = None
    curated_normal_bams = None
    curated_normal_ids = None

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        run_ids = self.run_ids if self.run_ids else [r.id for r in get_request_id_runs(self.request_id)]

        # Get all duplex bam ports for these runs
        access_duplex_output_ports = Port.objects.filter(
            name='duplex_bams',
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )
        # Each port is a list, so need a double list comprehension here
        all_access_output_records = [f for p in access_duplex_output_ports for f in p.value]
        # These are port objects, they don't have a metadata field
        tumors_to_run = self.parse_tumors_to_run(all_access_output_records)

        # Todo: how to know which sequencer's default normal to use?
        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME)[0]

        # Cache a set of fillout bams from this request for genotyping (we only need to do this query once)
        curated_normals_metadata = FileMetadata.objects.filter(
            file__file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG
        )
        curated_normal_bams = [f for f in curated_normals_metadata]
        self.curated_normal_ids = [f.metadata['snv_pipeline_id'] for f in curated_normals_metadata]
        self.curated_normal_bams = [
            {
                'class': 'File',
                'location': 'juno://' + b.file.path
            } for b in curated_normal_bams
        ]
        if self.request_id:
            self.fillout_unfiltered_normals = File.objects.filter(
                file_name__contains=NORMAL_SAMPLE_SEARCH,
                file_name__endswith=UNFILTERED_BAM_SEARCH,
                port__run__tags__requestId__startswith=self.request_id.split('_')[0]
            ) \
            .distinct('file_name') \
            .order_by('file_name', '-created_date')

            self.fillout_duplex_tumors = File.objects.filter(
                file_name__contains=TUMOR_SAMPLE_SEARCH,
                file_name__endswith=DUPLEX_BAM_SEARCH,
                port__run__tags__requestId=self.request_id
            ) \
            .distinct('file_name') \
            .order_by('file_name', '-created_date')

            self.fillout_simplex_tumors = File.objects.filter(
                file_name__contains=TUMOR_SAMPLE_SEARCH,
                file_name__endswith=SIMPLEX_BAM_SEARCH,
                port__run__tags__requestId=self.request_id
            ) \
            .distinct('file_name') \
            .order_by('file_name', '-created_date')

            # Evaluate the queryset so that the cache is populated for later queries which use slicing / LIMIT
            # https://docs.djangoproject.com/en/3.1/topics/db/queries/#when-querysets-are-not-cached
            list(self.fillout_unfiltered_normals)
            list(self.fillout_duplex_tumors)
            list(self.fillout_simplex_tumors)

        # Gather input Files / Metadata
        sample_infos = []
        for tumor_sample_id in tumors_to_run:
            sample_info = self.create_sample_info(tumor_sample_id)
            sample_info['normal_bam'] = normal_bam
            sample_infos.append(sample_info)

        # Format input templates
        sample_inputs = []
        for sample_info in sample_infos:
            sample_input = self.construct_sample_inputs(**sample_info)
            sample_inputs.append(sample_input)

        return sample_inputs

    def parse_tumors_to_run(self, duplex_file_output_records):
        """
        Extract the sample ID from a file's path in the output port

        Needs to support parsing from Record Ports generated by ACCESS_pipeline.cwl,
        as well as simple File Ports created manually through register_local_files.py

        :param duplex_file_output_records:
        :return:
        """
        tumor_sample_ids = []

        for r in duplex_file_output_records:
            if 'file' in r:
                basename = r['file']['basename']
            else:
                basename = r['basename']

            # Skip normal samples
            if NORMAL_SAMPLE_SEARCH in basename:
                continue
            sample_id = basename.split('/')[-1].split('_cl_aln_srt')[0]
            tumor_sample_ids.append(sample_id)

        return tumor_sample_ids

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

        # Get the Matched, Unfiltered, Normal BAM
        matched_normal_unfiltered_bam, matched_normal_unfiltered_id = \
            get_unfiltered_matched_normal(patient_id, self.request_id)

        # Get genotyping bams for Unfiltered Normal samples from the same Study
        geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids = \
            self.get_normal_geno_samples(tumor_sample_id, matched_normal_unfiltered_id)

        # Get genotyping bams for Simplex and Duplex Tumor samples from the same Patient or in the same Capture
        geno_samples_duplex, geno_samples_simplex = self.get_geno_samples(
            tumor_sample_id,
            tumor_duplex_bam,
            tumor_simplex_bam,
            matched_normal_unfiltered_id
        )

        capture_samples_duplex_sample_ids = [s.file_name.split('_cl_aln_srt')[0] for s in geno_samples_duplex]
        capture_samples_simplex_sample_ids = [s.file_name.split('_cl_aln_srt')[0] for s in geno_samples_simplex]

        # SNV pipeline requires that all samples have simplex and duplex bams
        if set(capture_samples_duplex_sample_ids) != set(capture_samples_simplex_sample_ids):
            msg = 'ACCESS SNV Operator Error: Duplex sample IDs not matched to Simplex sample IDs'
            raise Exception(msg)

        # Add in any DMP ACCESS samples
        dmp_matched_duplex_tumors,\
        dmp_matched_simplex_tumors,\
        dmp_matched_duplex_sample_ids,\
        dmp_matched_simplex_sample_ids = self.get_dmp_matched_patient_geno_samples(patient_id)

        geno_samples_duplex = geno_samples_duplex + dmp_matched_duplex_tumors
        geno_samples_simplex = geno_samples_simplex + dmp_matched_simplex_tumors
        geno_samples_duplex_sample_ids = capture_samples_duplex_sample_ids + dmp_matched_duplex_sample_ids
        geno_samples_simplex_sample_ids = capture_samples_simplex_sample_ids + dmp_matched_simplex_sample_ids

        sample_info = {
            'tumor_sample_id': tumor_sample_id,
            'tumor_duplex_bam': tumor_duplex_bam,
            'tumor_simplex_bam': tumor_simplex_bam,
            'matched_normal_unfiltered': matched_normal_unfiltered_bam,
            'matched_normal_unfiltered_id': matched_normal_unfiltered_id,
            'geno_samples_duplex': geno_samples_duplex,
            'geno_samples_simplex': geno_samples_simplex,
            'geno_samples_normal_unfiltered': geno_samples_normal_unfiltered,
            'geno_samples_normal_unfiltered_sample_ids': geno_samples_normal_unfiltered_sample_ids,
            'geno_samples_duplex_sample_ids': geno_samples_duplex_sample_ids,
            'geno_samples_simplex_sample_ids': geno_samples_simplex_sample_ids,
        }

        return sample_info

    def get_normal_geno_samples(self, tumor_sample_id, matched_normal_unfiltered_id):
        """
        20 first Normal fillout samples

        :return:
        """
        geno_samples_normal_unfiltered = self.fillout_unfiltered_normals[:20]
        logger.info("Adding {} fillout samples to SNV run for sample {}:".format(len(geno_samples_normal_unfiltered), tumor_sample_id))
        logger.info([s.file_name for s in geno_samples_normal_unfiltered])

        # Exclude matched normal bam
        if matched_normal_unfiltered_id:
            geno_samples_normal_unfiltered = [s for s in geno_samples_normal_unfiltered if not s.file_name.startswith(matched_normal_unfiltered_id)]

        geno_samples_normal_unfiltered_sample_ids = [s.file_name.split('_cl_aln_srt')[0] for s in geno_samples_normal_unfiltered]
        return geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids

    def get_geno_samples(self, tumor_sample_id, tumor_duplex_bam, tumor_simplex_bam, matched_normal_id):
        """
        Use the initial fastq metadata to get the capture of the sample,
        then, based on this capture ID, find tumor and matched normal simplex and duplex bams for genotyping

        Also include any tumor samples from the same patie4nt

        Limits to 40 samples (or 80 bams, because each has Simplex and Duplex)

        Todo: put metadata on the Bams themselves

        :param tumor_sample_id: str
        :return:
        """
        # Get capture ID
        capture_id = None
        sample_ids = []
        sample_fastq = FileRepository.filter(
            file_type='fastq',
            metadata={'sampleName': tumor_sample_id}
        )
        if len(sample_fastq) >= 1:
            capture_id = sample_fastq[0].metadata['captureName']

            # Get samples IDs from this capture from fastqs with this capture ID
            sample_id_fastqs = FileRepository.filter(
                file_type='fastq',
                metadata={'captureName': capture_id}
            )
            sample_ids = list(set([f.metadata['sampleName'] for f in sample_id_fastqs]))
            # Don't double-genotype the main sample
            sample_ids.remove(tumor_sample_id)

        if len(sample_ids) == 0 or not capture_id:
            duplex_capture_samples = []
            simplex_capture_samples = []
        else:
            capture_q = Q(
                *[('file_name__startswith', id) for id in sample_ids],
                _connector=Q.OR
            )

            duplex_capture_q = (Q(file_name__endswith=DUPLEX_BAM_SEARCH) & capture_q)
            simplex_capture_q = (Q(file_name__endswith=SIMPLEX_BAM_SEARCH) & capture_q)

            duplex_capture_samples = File.objects.filter(duplex_capture_q)\
                .distinct('file_name')\
                .order_by('file_name', '-created_date')\
                .exclude(file_name=tumor_duplex_bam.file_name)\
                .exclude(file_name__startswith=matched_normal_id)
            simplex_capture_samples = File.objects.filter(simplex_capture_q)\
                .distinct('file_name')\
                .order_by('file_name', '-created_date')\
                .exclude(file_name=tumor_simplex_bam.file_name)\
                .exclude(file_name__startswith=matched_normal_id)

            duplex_capture_samples = list(duplex_capture_samples)
            simplex_capture_samples = list(simplex_capture_samples)

        # Add patient matched Tumors samples
        patient_id = '-'.join(tumor_sample_id.split('-')[0:2])
        matched_tumor_search = patient_id + TUMOR_SAMPLE_SEARCH
        duplex_matched_q =  Q(file_name__endswith=DUPLEX_BAM_SEARCH) & Q(file_name__startswith=matched_tumor_search)
        simplex_matched_q =  Q(file_name__endswith=SIMPLEX_BAM_SEARCH) & Q(file_name__startswith=matched_tumor_search)

        duplex_matched_samples = File.objects.filter(duplex_matched_q) \
            .distinct('file_name') \
            .order_by('file_name', '-created_date') \
            .exclude(file_name=tumor_duplex_bam.file_name) \
            .exclude(file_name__startswith=matched_normal_id)
        simplex_matched_samples = File.objects.filter(simplex_matched_q) \
            .distinct('file_name') \
            .order_by('file_name', '-created_date') \
            .exclude(file_name=tumor_simplex_bam.file_name) \
            .exclude(file_name__startswith=matched_normal_id)

        duplex_geno_samples = list(duplex_matched_samples) + list(duplex_capture_samples)
        simplex_geno_samples = list(simplex_matched_samples) + list(simplex_capture_samples)

        if len(duplex_geno_samples) < 20:
            num_geno_samples_to_add = 20 - len(duplex_geno_samples)
            duplex_geno_samples_to_add = self.fillout_duplex_tumors[:num_geno_samples_to_add]
            simplex_geno_samples_to_add = self.fillout_simplex_tumors[:num_geno_samples_to_add]
            # Remove the main tumor sample
            duplex_geno_samples_to_add = [s for s in duplex_geno_samples_to_add if s.file_name != tumor_duplex_bam.file_name]
            simplex_geno_samples_to_add = [s for s in simplex_geno_samples_to_add if s.file_name != tumor_simplex_bam.file_name]
            duplex_geno_samples += duplex_geno_samples_to_add
            simplex_geno_samples += simplex_geno_samples_to_add
            # Deduplicate
            duplex_geno_samples = list(set(duplex_geno_samples))
            simplex_geno_samples = list(set(simplex_geno_samples))

        return duplex_geno_samples, simplex_geno_samples

    def get_dmp_matched_patient_geno_samples(self, patient_id):
        """
        Find DMP ACCESS samples for genotyping

        :param patient_id: str - CMO sample ID (C-123ABC)
        :return: (QuerySet<File> - Duplex Bams, QuerySet<File> - Simplex Bams, str[] duplex samples IDs,
            str[] simplex sample IDs)
        """
        matched_duplex_tumors_dmp = FileMetadata.objects.filter(
            metadata__cmo_assay='ACCESS_V1_0',
            metadata__patient__cmo=patient_id.replace('C-', ''),
            metadata__type='T',
            file__path__endswith=DMP_DUPLEX_REGEX
        )
        matched_duplex_tumors_dmp = [b.file for b in matched_duplex_tumors_dmp]
        matched_duplex_sample_ids_dmp = [b.file_name.replace('-duplex.bam', '') for b in matched_duplex_tumors_dmp]

        matched_simplex_tumors_dmp = FileMetadata.objects.filter(
            metadata__cmo_assay='ACCESS_V1_0',
            metadata__patient__cmo=patient_id.replace('C-', ''),
            metadata__type='T',
            file__path__endswith=DMP_SIMPLEX_REGEX
        )
        matched_simplex_tumors_dmp = [b.file for b in matched_simplex_tumors_dmp]
        matched_simplex_sample_ids_dmp = [b.file_name.replace('-simplex.bam', '') for b in matched_simplex_tumors_dmp]

        return matched_duplex_tumors_dmp, matched_simplex_tumors_dmp, matched_duplex_sample_ids_dmp, matched_simplex_sample_ids_dmp

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        self.request_id = get_request_id(self.run_ids, self.request_id)
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

    def construct_sample_inputs(self, normal_bam, tumor_sample_id, tumor_duplex_bam, tumor_simplex_bam, matched_normal_unfiltered,
                                matched_normal_unfiltered_id, geno_samples_duplex, geno_samples_simplex, geno_samples_duplex_sample_ids,
                                geno_samples_simplex_sample_ids, geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids):
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

            normal_bams = [{
                "class": "File",
                "location": 'juno://' + normal_bam.path
            }]
            normal_sample_names = [ACCESS_DEFAULT_NORMAL_ID]

            genotyping_bams = [
                {"class": "File", "location": 'juno://' + tumor_duplex_bam.path},
                {"class": "File", "location": 'juno://' + tumor_simplex_bam.path}
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
            if len(geno_samples_duplex) > 0:
                genotyping_bams += [
                    {"class": "File", "location": 'juno://' + b.path} for b in geno_samples_duplex
                ]
                genotyping_bams += [
                    {"class": "File", "location": 'juno://' + b.path} for b in geno_samples_simplex
                ]
                genotyping_bams_ids += geno_samples_duplex_sample_ids
                genotyping_bams_ids += [i + '-SIMPLEX' for i in geno_samples_simplex_sample_ids]

            # Additional unfiltered normals may be available
            if len(geno_samples_normal_unfiltered) > 0:
                genotyping_bams += [
                    {"class": "File", "location": 'juno://' + b.path} for b in geno_samples_normal_unfiltered
                ]
                genotyping_bams_ids += geno_samples_normal_unfiltered_sample_ids

            genotyping_bams += self.curated_normal_bams
            genotyping_bams_ids += self.curated_normal_ids

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
