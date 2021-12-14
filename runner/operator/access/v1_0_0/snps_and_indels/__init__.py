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
from runner.run.objects.run_creator_object import RunCreator
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

    @staticmethod
    def is_tumor_bam(file):
        if not file.file_name.endswith('.bam'):
            return False
        t_n_timepoint = file.file_name.split('-')[2]
        return not t_n_timepoint[0] == 'N'

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator

        :return: list of json_objects
        """
        run_ids = self.run_ids if self.run_ids else [r.id for r in get_request_id_runs(self.request_id)]

        # Get all duplex / simplex bam ports for these runs
        duplex_output_ports = Port.objects.filter(
            name__in=['duplex_bams', 'fgbio_filter_consensus_reads_duplex_bam'],
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )
        simplex_output_ports = Port.objects.filter(
            name__in=['simplex_bams', 'fgbio_postprocessing_simplex_bam'],
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )

        duplex_tumor_bams = [f for p in duplex_output_ports for f in p.files.all() if self.is_tumor_bam(f)]
        simplex_tumor_bams = [f for p in simplex_output_ports for f in p.files.all() if self.is_tumor_bam(f)]

        def make_pairs(d, s):
            paired = []
            for di in d:
                for si in s:
                    if di.file_name.rstrip('-duplex.bam') == si.file_name.rstrip('-simplex.bam'):
                        paired.append((di, si))
            return paired

        # Make sure simplex bams are paired with duplex of same sample ID
        tumor_bams = make_pairs(duplex_tumor_bams, simplex_tumor_bams)

        # Todo: how to know which sequencer's default normal to use?
        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME)[0]

        # Cache a set of fillout bams from this request for genotyping (we only need to do this query once)
        curated_normals_metadata = FileMetadata.objects.filter(
            file__file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG
        )
        curated_normal_bams = [f for f in curated_normals_metadata]
        self.curated_normal_ids = [f.metadata['snv_pipeline_id'] for f in curated_normals_metadata]
        self.curated_normal_bams = [self._create_cwl_bam_object(b.file) for b in curated_normal_bams]

        if self.request_id:
            # Todo: need to limit these to just Nucleo bams?
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
        for d, s in tumor_bams:
            sample_info = self.create_sample_info(d, s)
            sample_info['normal_bam'] = normal_bam
            sample_infos.append(sample_info)

        # Format input templates
        sample_inputs = []
        for sample_info in sample_infos:
            sample_input = self.construct_sample_inputs(**sample_info)
            sample_inputs.append(sample_input)

        return sample_inputs


    def create_sample_info(self, tumor_duplex_bam, tumor_simplex_bam):
        """
        Query DB for all relevant files / metadata necessary for SNV pipeline input:

        - Tumor Duplex Bam
        - Tumor Simplex Bam
        - Matched Normal Unfiltered bam (from IGO / DMP or None) (external code)
        - Other Tumor Duplex bams from same patient or capture (for genotyping)
        - Other Tumor Simplex bams from same patient or capture (for genotyping)

        :return:
        """
        tumor_sample_id = self.extract_sample_id(tumor_duplex_bam)
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

        capture_samples_duplex_sample_ids = [self.extract_sample_id(s) for s in geno_samples_duplex]
        capture_samples_simplex_sample_ids = [self.extract_sample_id(s) for s in geno_samples_simplex]

        # Use sample IDs to remove duplicates from normal geno samples
        geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids = self._remove_normal_dups(
            geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids,
            capture_samples_duplex_sample_ids)

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

    @staticmethod
    def extract_sample_id(s):
        if '_cl_aln_srt' in s.file_name:
            ret = s.file_name.split('_cl_aln_srt')[0]
        else:
            ret = s.filemetadata_set.first().metadata['sampleName']
        return ret

    def _remove_normal_dups(self, geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids,
                            capture_samples_duplex_sample_ids):
        """
        Make sure none of the normals are already present in duplex genotyping samples (GBCMS can not have
        duplicate sample IDs)

        :param geno_samples_normal_unfiltered:
        :param geno_samples_normal_unfiltered_sample_ids:
        :param capture_samples_duplex_sample_ids:
        :return:
        """
        deduped = []
        deduped_ids = []
        for i, s in enumerate(geno_samples_normal_unfiltered_sample_ids):
            if not any([sid in s for sid in capture_samples_duplex_sample_ids]):
                deduped_ids.append(s)
                deduped.append(geno_samples_normal_unfiltered[i])
        return deduped, deduped_ids

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

        geno_samples_normal_unfiltered_sample_ids = [self.extract_sample_id(s) for s in geno_samples_normal_unfiltered]
        return geno_samples_normal_unfiltered, geno_samples_normal_unfiltered_sample_ids

    def get_geno_samples(self, tumor_sample_id, tumor_duplex_bam, tumor_simplex_bam, matched_normal_id):
        """
        Use the initial fastq metadata to get the capture of the sample,
        then, based on this capture ID, find tumor and matched normal simplex and duplex bams for genotyping

        Also include any tumor samples from the same patient

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

            if capture_id:
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

        # Deduplicate based on PK
        duplex_geno_samples = list(set(duplex_geno_samples))
        simplex_geno_samples = list(set(simplex_geno_samples))
        # Deduplicate based on file name
        duplex_geno_samples, simplex_geno_samples = self._remove_dups_by_file_name(duplex_geno_samples, simplex_geno_samples)

        return duplex_geno_samples, simplex_geno_samples

    def _remove_dups_by_file_name(self, duplex_geno_samples, simplex_geno_samples):
        """
        Simple util to avoid Genotyping same sample twice
        (when bams come from different runs and can't be
        de-duplicated based on PK)

        :return:
        """
        duplex_geno_samples_dedup_ids = set()
        duplex_geno_samples_dedup = []
        for s in duplex_geno_samples:
            if not s.file_name in duplex_geno_samples_dedup_ids:
                duplex_geno_samples_dedup_ids.add(s.file_name)
                duplex_geno_samples_dedup.append(s)
        simplex_geno_samples_dedup_ids = set()
        simplex_geno_samples_dedup = []
        for s in simplex_geno_samples:
            if not s.file_name in simplex_geno_samples_dedup_ids:
                simplex_geno_samples_dedup_ids.add(s.file_name)
                simplex_geno_samples_dedup.append(s)
        return duplex_geno_samples_dedup, simplex_geno_samples_dedup

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
            RunCreator(
                **{
                    'name': "ACCESS LEGACY SNV M1: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
                    'app': self.get_pipeline_id(),
                    'inputs': job,
                    'tags': {
                        'requestId': self.request_id,
                        'cmoSampleIds': job["tumor_sample_names"],
                        'patientId': '-'.join(job["tumor_sample_names"][0].split('-')[0:2])
                    }
                }
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
            tumor_bams = [self._create_cwl_bam_object(tumor_duplex_bam)]

            matched_normal_ids = [matched_normal_unfiltered_id]
            normal_bams = [self._create_cwl_bam_object(normal_bam)]
            normal_sample_names = [ACCESS_DEFAULT_NORMAL_ID]

            genotyping_bams = [
                self._create_cwl_bam_object(tumor_duplex_bam),
                self._create_cwl_bam_object(tumor_simplex_bam)
            ]
            genotyping_bams_ids = [tumor_sample_id, tumor_sample_id + '-SIMPLEX']

            # Matched Normal may or may not be available for genotyping
            if matched_normal_unfiltered:
                genotyping_bams += [self._create_cwl_bam_object(matched_normal_unfiltered)]
                genotyping_bams_ids += [matched_normal_unfiltered_id]

            # Additional matched Tumors may be available
            if len(geno_samples_duplex) > 0:
                genotyping_bams += [self._create_cwl_bam_object(b) for b in geno_samples_duplex]
                genotyping_bams += [self._create_cwl_bam_object(b) for b in geno_samples_simplex]
                genotyping_bams_ids += geno_samples_duplex_sample_ids
                genotyping_bams_ids += [i + '-SIMPLEX' for i in geno_samples_simplex_sample_ids]

            # Additional unfiltered normals may be available
            if len(geno_samples_normal_unfiltered) > 0:
                genotyping_bams += [self._create_cwl_bam_object(b) for b in geno_samples_normal_unfiltered]
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

    @staticmethod
    def _create_cwl_bam_object(bam):
        """
        Util function to create a simple CWL File object from a bam with a path attribute

        :param bam:
        :return:
        """
        return {
            "class": "File",
            "location": "juno://" + bam.path
        }
    