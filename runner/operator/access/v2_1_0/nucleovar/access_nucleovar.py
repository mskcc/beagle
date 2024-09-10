import copy
import os
import csv
import logging
from django.db.models import Q
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.models import Pipeline
import runner.operator.chronos_operator.bin.tempo_patient as patient_obj
from notifier.models import JobGroup
from notifier.events import OperatorRequestEvent, ChronosMissingSamplesEvent
from notifier.tasks import send_notification
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File
from runner.models import Port, RunStatus
from file_system.models import FileMetadata
from runner.models import RunStatus, Port, Run
import json 

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)
ACCESS_CURATED_BAMS_FILE_GROUP_SLUG = "access_curated_normals"
ACCESS_DEFAULT_NORMAL_ID = "DONOR22-TP"
ACCESS_DEFAULT_NORMAL_FILENAME = "DONOR22-TP_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
NORMAL_SAMPLE_SEARCH = "-N0"
TUMOR_SAMPLE_SEARCH = "-L0"
DUPLEX_BAM_SEARCH = "__aln_srt_IR_FX-duplex.bam"
SIMPLEX_BAM_SEARCH = "__aln_srt_IR_FX-simplex.bam"
UNFILTERED_BAM_SEARCH = "__aln_srt_IR_FX.bam"
DMP_DUPLEX_REGEX = "-duplex.bam"
DMP_SIMPLEX_REGEX = "-simplex.bam"
DUPLEX_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
SIMPLEX_BAM_STEM = "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"
class NucleoVarOperator(Operator):

    def find_request_bams(run):
        """
        Find simplex and duplex bams from a request's nucleo run
        - run_ids: run_ids from a request's nucleo run

        :return: list of paired simplex and duplex bams and normal bam
        """
        nucleo_output_port_names = [
            "uncollapsed_bam",
            "fgbio_group_reads_by_umi_bam",
            "fgbio_collapsed_bam",
            "fgbio_filter_consensus_reads_duplex_bam",
            "fgbio_postprocessing_simplex_bam",
        ]
        bams = {}
        for o in nucleo_output_port_names:
            # We are running a multi-sample workflow on just one sample,
            # so we create single-element lists here
            bam = parse_nucleo_output_ports(run, o)
            bams[o] = bam
        
        return bams

    def parse_nucleo_output_ports(run, port_name):
        bam_bai = Port.objects.get(name=port_name, run=run.pk)
        if not len(bam_bai.files.all()) in [1, 2]:
            raise Exception("Port {} for run {} should have just 1 bam or 1 (bam/bai) pair".format(port_name, run.id))
        bam = [b for b in bam_bai.files.all() if b.file_name.endswith(".bam")][0]
        return bam
    
    def is_tumor_bam(file):
        if not file.endswith(".bam"):
            return False
        t_n_timepoint = file.split("-")[2]
        return not t_n_timepoint[0] == "N"

    def find_request_bams(run):
        """
        Find simplex and duplex bams from a request's nucleo run
        - run_ids: run_ids from a request's nucleo run

        :return: list of paired simplex and duplex bams and normal bam
        """
        nucleo_output_port_names = [
            "uncollapsed_bam",
            "fgbio_group_reads_by_umi_bam",
            "fgbio_collapsed_bam",
            "fgbio_filter_consensus_reads_duplex_bam",
            "fgbio_postprocessing_simplex_bam",
        ]
        bams = {}
        for o in nucleo_output_port_names:
            # We are running a multi-sample workflow on just one sample,
            # so we create single-element lists here
            bam = self.parse_nucleo_output_ports(run, o)
            bams[o] = bam
        
        return bams

    
    def find_curated_normal_bams():
        """
        Find curated normal bams from access curated bam file group

        :return: list of curated normal bams 
        """
        def split_duplex_simplex(files):
            '''
            given a list split file paths using -simplex and -duplex root
            :param files: a list of simplex/duplex file path 
            :return: two lists of file paths: one for simplex, one for duplex
            '''
            simplex = [] 
            duplex = [] 
            for f in files:
                if f.file_name.endswith('-simplex.bam'):
                    simplex.append(f)
                if f.file_name.endswith('-duplex.bam'):
                    duplex.append(f)
                else:
                    ValueError('Expecting a list of duplex and simplex bams')  
            return duplex, simplex

        def make_pairs(d, s):
            paired = []
            for di in d:
                for si in s:
                    if di.file_name.rstrip("-duplex.bam") == si.file_name.rstrip("-simplex.bam"):
                        paired.append((di, si))
            return paired  
        # Cache a set of fillout bams from this request for genotyping (we only need to do this query once)
        curated_normals_metadata = FileMetadata.objects.filter(
            file__file_group__slug=ACCESS_CURATED_BAMS_FILE_GROUP_SLUG
        )
        curated_normal_bams = [f.file for f in curated_normals_metadata]
        d,s = split_duplex_simplex(curated_normal_bams)
        curated_normal_bams = make_pairs(d, s)
        return curated_normal_bams
    

    def get_jobs(self):
        """
        get_job information tor run NucleoVar Pipeline
        - self: NucleoVarOperator(Operator)

        :return: return RunCreator Objects with NucleoVar information
        """
        # Run Information
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = pipeline.output_directory
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        # If no request_id, start happens from runs chaining
        # else manual start
        if not self.request_id:
            most_recent_runs_for_request = Run.objects.filter(pk__in=self.run_ids)
            self.request_id = most_recent_runs_for_request[0].tags["igoRequestId"]
        else:
            runs = self.get_request_id_runs(self.request_id, ["access v2 nucleo"])
        # Get Bams generate by Access V2 Nucleo
        bams = []
        for run in runs:
            bams.append(self.find_request_bams(run))

        # TUMOR
        tumor_bams = [(b['fgbio_filter_consensus_reads_duplex_bam'], b['fgbio_postprocessing_simplex_bam']) for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_duplex_bam'].file_name)]
        
        # FILLOUT NORMAL AND TUMOR 
        fillout_simplex_tumors = [b['fgbio_postprocessing_simplex_bam'] for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_simplex_bam'].file_name)]
        fillout_duplex_tumors = [b['fgbio_filter_consensus_reads_duplex_bam'] for b in bams if self.is_tumor_bam(b['fgbio_postprocessing_simplex_bam'].file_name)]
        fillout_unfiltered_normals = [b['uncollapsed_bam'] for b in bams if not self.is_tumor_bam(b['uncollapsed_bam'].file_name)]
        
        # NORMAL BAM
        normal_bam = File.objects.filter(file_name=ACCESS_DEFAULT_NORMAL_FILENAME)[0]
        
        # CURATED NORMAL
        curated_normal_bams = self.find_curated_normal_bams()

        # SAMPLE INFO 
        sample_infos = []
        tumor_bams = tumor_bams[0:1]
        for d, s in tumor_bams:
            sample_info = self.create_sample_info(d, s, bams)
            sample_info["normal_bam"] = [normal_bam]
            sample_info["tumor_bam"] = [(d, s)]
            sample_infos.append(sample_info)
        
        return [RunCreator(**job) for job in jobs]
    