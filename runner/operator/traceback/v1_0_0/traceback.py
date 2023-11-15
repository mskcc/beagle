import os
import json
import uuid
import logging
from pathlib import Path
from jinja2 import Template
from beagle import settings
from runner.operator.operator import Operator
from runner.models import RunStatus, Port, Run, OperatorRun
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File, FileGroup, FileType
from file_system.repository import FileRepository
from runner.models import Pipeline
from file_system.helper.access_helper import CmoDMPManifest
from runner.operator.access import get_request_id, get_request_id_runs, create_cwl_file_object
import csv, re

logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))


meta_fields = [
    "igoId",
    settings.CMO_SAMPLE_TAG_METADATA_KEY,
    settings.CMO_SAMPLE_NAME_METADATA_KEY,
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,
    settings.PATIENT_ID_METADATA_KEY,
    "investigatorSampleId",
    settings.ONCOTREE_METADATA_KEY,
    "tumorOrNormal",
    "tissueLocation",
    settings.SAMPLE_CLASS_METADATA_KEY,
    "sampleOrigin",
    "preservation",
    "collectionYear",
    "sex",
    "species",
    "tubeId",
    "cfDNA2dBarcode",
    "baitSet",
    "qcReports",
    "barcodeId",
    "barcodeIndex",
    settings.LIBRARY_ID_METADATA_KEY,
    "libraryVolume",
    "libraryConcentrationNgul",
    "dnaInputNg",
    "captureConcentrationNm",
    "captureInputNg",
    "captureName",
]


class AccessManifestOperator(Operator):
    """
    Operator to create a manifest report (merged dmp and fastq metadata) for a given access request.
    """


    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        # TODO: NORMALS or NOT
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        self.OUTPUT_DIR = pipeline.output_directory
        # get request id
        self.request_ids = get_request_id(self.run_ids, self.request_id)
        # get fastq metadata for a given request
        lims_fastq = FileRepository.filter(file_group="b54d035d-f63c-4ea8-86fb-9dbc976bb7fe")
        # access_fastq = lims_fastq.filter(file__request_id=self.request_ids)
        access_fastq = lims_fastq.filter(file__request_id="13893_N")
        cmoPatientId = list(set(access_fastq.values_list('metadata__cmoPatientId', flat = True)))
        cmoPatientId_trunc = [patient.strip('C-') for patient in cmoPatientId]

        # CMO ACCESS mafs and bams 
        cmo_bams_xs_tumor, cmo_bams_xs_normal = self.find_cmo_xs_bams(cmoPatientId)
        cmo_mafs_xs = self.find_cmo_xs_mafs(cmoPatientId)
        
        # TODO MAF/BAM CHECK FOR ACCESS 
        # CMO IMPACT BAMS 
        cmo_bams_imp_tumor, cmo_bams_imp_normal = self.find_cmo_imp_bams(cmoPatientId, cmoPatientId_trunc)
        cmo_mafs_imp = self.find_cmo_imp_mafs(cmoPatientId, cmoPatientId_trunc)
        impact_samples_tumor = list(cmo_bams_imp_tumor.keys())
        sample_level_mafs = self.subset_helix_maf(impact_samples_tumor, cmo_mafs_imp)
        # CMO IMPACT BAMS 
        # only use bams that have mafs 
        usable_tumors = list(set(cmo_bams_imp_tumor.keys()).intersection(set(sample_level_mafs.keys())))
        sample_level_mafs = {k:v for k,v in sample_level_mafs.items() if k in usable_tumors}
        impact_samples_tumor = {k:v for k,v in impact_samples_tumor.items() if k in usable_tumors}


        # DMP BAM (IMPACT AND XS)
        dmp_bams = FileRepository.filter(file_group=settings.DMP_BAM_FILE_GROUP)
        # subset DMP BAM file group to patients in the provided requests
        pDmpsTumor = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trunc, metadata__type='T')
        pDmpsNormal = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trunc, metadata__type='N')
        pDmpsTumorBam = [r.file.path for r in pDmpsTumor] 
        pDmpsNormalBam = [r.file.path for r in pDmpsNormal] 
        #TODO standard BAM for XS normals and simplex / duplex for XS tumors 
        #NOTE string method will have to be used we only track standards in Voyager
        # DMP BAM (IMPACT AND XS)
        #TODO MAF/BAM check for DMP 
        dmp_samples_tumor = list(pDmpsTumor.values_list('metadata__sample', flat = True))
        sample_level_mafs_dmp = subset_dmp_maf(dmp_samples_tumor)
        
        # # create job input json with manifest path
        # job = self.construct_sample_input(manifest_path)
        # # submit file to RunCreator
        # # uses a cwl that returns the created manifest csv: https://github.com/msk-access/cwl_pass_through
        # return [
        #     RunCreator(
        #         **{
        #             "name": "Manifest Operator %s" % (self.request_id),
        #             "app": self.get_pipeline_id(),
        #             "inputs": job,
        #             "tags": {
        #                 settings.REQUEST_ID_METADATA_KEY: self.request_id,
        #             },
        #         }
        #     )
        # ]


    def read_dmp_combined_maf(self):
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())
        
        return 0 
    def dict_list_append(d, key, item):
        if d.get(key) is None:
            d[key] = [item]
        else:
            d[key].append(item)
        return d

    def write_to_file(self, fname, s):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = os.path.join(self.OUTPUT_DIR, fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        self.register_tmp_file(output)
        return output
    
    def write_to_file(fname, s):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = os.path.join("/home/buehlere/voyager_test", fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        return output

    def register_tmp_file(self, path):
        fname = os.path.basename(path)
        temp_file_group = FileGroup.objects.get(slug="impact_maf_traceback")
        file_type = FileType.objects.get(name="txt")
        try:
            File.objects.get(path=path)
        except:
            print("Registering temp file %s" % path)
            f = File(file_name=fname, path=path, file_type=file_type, file_group=temp_file_group)
            f.save()

    def find_cmo_xs_bams(self, cmoPatientId):
        """
        creates manifest csv, write contents to file
        :return: manifest csv path
        """
        # get DMP BAM file group
        # xs_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
        xs_fastqs= lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
        xs_fastq_tumor = xs_fastqs.filter(metadata__tumorOrNormal="Tumor")
        xs_fastq_norm = xs_fastqs.filter(metadata__tumorOrNormal="Normal")
        xs_requests = list(set([fastq.metadata["igoRequestId"] for fastq in xs_fastqs]))
        xs_samples_tumor = list(set([fastq.metadata["cmoSampleName"] for fastq in xs_fastq_tumor]))
        xs_samples_normal= list(set([fastq.metadata["cmoSampleName"] for fastq in xs_fastq_norm]))
        # xs_runs = self.find_recent_runs(xs_requests, ["59a8d3f6-d54d-46d6-a412-5f4f3b25f22d","48008842-625e-4af5-827f-fb4b92d7e0e7"])
        xs_runs = self.find_recent_runs_xs(xs_requests, "AccessLegacyOperator", xs_samples_tumor + xs_samples_tumor)
        xs_bams_tumor = self.find_run_files_xs(xs_runs, ['simplex_bams','duplex_bams'], xs_samples_tumor)
        xs_bams_norm = self.find_run_files_xs(xs_runs, ['standard_bams'], xs_samples_normal)
        return xs_bams_tumor, xs_bams_norm
    
    def find_cmo_xs_mafs(self, cmoPatientId):
        # xs_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
        xs_fastqs= lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
        xs_fastq_tumor = xs_fastqs.filter(metadata__tumorOrNormal="Tumor")
        xs_fastq_norm = xs_fastqs.filter(metadata__tumorOrNormal="Normal")
        xs_requests = list(set([fastq.metadata["igoRequestId"] for fastq in xs_fastqs]))
        xs_samples_tumor = list(set([fastq.metadata["cmoSampleName"] for fastq in xs_fastq_tumor]))
        xs_runs_maf = self.find_recent_runs_xs(xs_requests, 
                                    "AccessLegacySNVOperator", 
                                    xs_samples_tumor)
        xs_mafs = self.find_run_files_xs(xs_runs_maf, ['final_filtered_maf'], xs_samples_tumor)
        return xs_mafs
        

    def find_cmo_imp_mafs(self, cmoPatientId, cmoPatientId_trunc):
        # xs_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
        impact_fastqs= lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*IMPACT.*")
        impact_fastq_tumor = impact_fastqs.filter(metadata__tumorOrNormal="Tumor")
        impact_fastq_norm = impact_fastqs.filter(metadata__tumorOrNormal="Normal")
        impact_requests = list(set([fastq.metadata["igoRequestId"] for fastq in impact_fastqs]))
        impact_samples_tumor = list(set([fastq.metadata["cmoSampleName"] for fastq in impact_fastq_tumor]))
        impact_runs_maf = self.find_recent_runs_helix(impact_requests, "HelixFiltersOperator*")
        impact_mafs = self.find_run_files_helix(impact_runs_maf, ['portal_dir'], cmoPatientId_trunc)
        # TODO: subset and combine mafs
        return impact_mafs
    
    def find_cmo_imp_bams(self, cmoPatientId, cmoPatientId_trunc):
        impact_fastq = lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*IMPACT.*")
        impact_fastq_tumor = impact_fastq.filter(metadata__tumorOrNormal="Tumor")
        impact_fastq_norm = impact_fastq.filter(metadata__tumorOrNormal="Normal")
        impact_samples_tumor = list(set([fastq.metadata["cmoSampleName"] for fastq in impact_fastq_tumor]))
        impact_samples_normal= list(set([fastq.metadata["cmoSampleName"] for fastq in impact_fastq_norm]))
        impact_requests = list(set([fastq.metadata["igoRequestId"] for fastq in impact_fastq]))
        impact_runs = self.find_recent_runs_argos(impact_requests, "ArgosOperator*", cmoPatientId_trunc)
        impact_bams_tumor = self.find_run_files_impact(impact_runs, ['tumor_bam'], cmoPatientId_trunc)
        impact_bams_norm = self.find_run_files_impact(impact_runs, ['normal_bam'], cmoPatientId_trunc)
        return impact_bams_tumor, impact_bams_norm

            
    def find_recent_runs_xs(requests, slug, samples):
        request_runs = []
        for request in requests:
            opRun = OperatorRun.objects.filter( status=RunStatus.COMPLETED,
                                               operator__slug__regex=slug)
            # opRunReq = self.query_from_dict(opRun, {'igoRequestId':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            opRunReq = query_from_dict(opRun, {'igoRequestId':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            try: 
                latest_runs = opRunReq.runs.all()
            except:
                continue
            for r in latest_runs:
                cmoSampleId = set(r.tags['cmoSampleIds'])
                if cmoSampleId.intersection(set(samples)):
                        request_runs.append(r.id)
        return request_runs
    
    def find_recent_runs_argos(requests, slug, patient):
        request_runs = []
        for request in requests:
            opRun = OperatorRun.objects.filter( status=RunStatus.COMPLETED,
                                               operator__slug__regex=slug)
            # opRunReq = self.query_from_dict(opRun, {'igoRequestId':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            opRunReq = query_from_dict(opRun, {'igoRequestId':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            try: 
                latest_runs = opRunReq.runs.all()
            except:
                continue
            for r in latest_runs:
                cmoSampleId_tumor = r.tags['sampleNameTumor']
                cmoSampleId_norm = r.tags['sampleNameNormal']
                try: 
                    cpidt = re.search(r'C(_|-)(\w{6})',cmoSampleId_tumor).group(2)
                except:
                    cpidt = "other"
                try:
                    cpidn = re.search(r'C(_|-)(\w{6})',cmoSampleId_norm).group(2)
                except:
                    cpidn = "other"
                pids = set([cpidt,cpidn])
                if pids.intersection(patient):
                        request_runs.append(r.id)
        return request_runs
    


    def find_recent_runs_helix(requests, slug):
        request_runs = []
        for request in requests:
            opRun = OperatorRun.objects.filter( status=RunStatus.COMPLETED,
                                               operator__slug__regex=slug)
            # opRunReq = self.query_from_dict(opRun, {'igoRequestId':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            opRunReq = query_from_dict(opRun, {'project_prefix':request}, "runs__tags__%s__contains").order_by('-finished_date').first()
            try: 
                latest_runs = opRunReq.runs.all()
            except:
                continue
            if len(latest_runs) == 1:
                request_runs.append(latest_runs[0].id)
            if len(latest_runs) > 1:
                argos_helix_last = latest_runs.order_by('-finished_date').first()
                request_runs.append(argos_helix_last.id)
        return request_runs

    def query_from_dict(queryset, dictionary, query_filter):
        query = {query_filter % key: val for (key, val) in dictionary.items()}
        return queryset.filter(**query)
    
    def find_run_files_impact(runs, ports, patients):
        file_match = {}
        for run in runs:
            file_port = Port.objects.filter(name__in=ports, 
                                                run__id=run, 
                                                run__status=RunStatus.COMPLETED)
            for port in file_port:
                file_name = port.value['basename']
                file_location = port.value['location']
                try: 
                    sbam_cpid = re.search(r's_C_(\w{6})_',file_name).group(1)
                except: 
                    sbam_cpid = None 
                try:
                    sbam_sample = re.search(r'(s_C_\w{6}_\w{4}_d\w*)\.',file_name).group(1)
                except: 
                    sbam_sample = None 
                if sbam_cpid in patients:
                        if file_match.get(sbam_sample) is None:
                            file_match[sbam_sample] = [file_location]
                        else:
                            file_match[sbam_sample].append(file_location)
        return file_match
    
    def find_run_files_xs(runs, ports, samples):
        file_match = {}
        for run in runs:
            file_port = Port.objects.filter(name__in=ports, 
                                                run__id=run, 
                                                run__status=RunStatus.COMPLETED)
            for port in file_port:
                files = port.value
            # find which cmo patient file this maps to and save in a dict
                for sfile in files:
                    try: 
                        file_name = sfile['file']['basename']
                        file_location = sfile['file']['location']
                    except:
                        file_name = sfile['basename']
                        file_location = sfile['location']
                    # sfile_cpid = re.search(r'C-(\w{6})-',file_name).group(1)
                    sfile_sample = re.search(r'(C-\w{6}-\w{4}-d\d{0,2})',file_name).group(1)
                    if sfile_sample in samples:
                            if file_match.get(sfile_sample) is None:
                                file_match[sfile_sample] = [file_location]
                            else:
                                file_match[sfile_sample].append(file_location)
        return file_match
    
    def subset_helix_maf(impact_samples, mut_paths):
        impact_match_maf = {}
        for sample in impact_samples:
            for path in mut_paths:
                # Open the TSV file for reading
                with open(path.strip("file:"), 'r') as tsvfile:
                        # Initialize a list to store the matching rows
                        matching_rows = []
                        # Read the file line by line
                        for i, line in enumerate(tsvfile):
                            columns = line.strip().split('\t') 
                            line = line.strip()  # Remove leading/trailing whitespace
                    
                            # If the line contains the header, add it to the matching rows
                            if i == 1:
                                matching_rows.append(line)
                            if i > 1:
                                # Check if the line matches the pattern
                                if re.match(sample, columns[15]):
                                    matching_rows.append(line)
                if len(matching_rows) > 1: 
                    # impact_maf_path = self.write_to_file(f"{patient}_data_mutations.txt",'\n'.join(matching_rows))
                    impact_maf_path = write_to_file(f"{sample}_data_mutations.txt",'\n'.join(matching_rows))
                    # self.dict_list_append(impact_match_maf,pattern, impact_maf_path)
                    # dict_list_append(impact_match_maf,sample, impact_maf_path)
                    if impact_match_maf.get(sample) is None:
                        impact_match_maf[sample] = [impact_maf_path]
                    else:
                        impact_match_maf[sample].append(impact_maf_path)
        return impact_match_maf

    def find_run_files_helix(runs, ports):
        file_match = []
        for run in runs:
            file_port = Port.objects.filter(name__in=ports, 
                                                run__id=run, 
                                                run__status=RunStatus.COMPLETED)
            for dir in file_port:
                listing = dir.value['listing']
                for file in listing:
                    if file['basename'] == 'data_mutations_extended.txt':
                        file_match.append(file['location'])
        return file_match
    
    def subset_dmp_maf(dmp_samples):
        dmp_match_maf = {}
        for sample in dmp_samples:
            # with open(settings.DMP_MUTATIONS, 'r') as tsvfile:
            #TODO Need to make the is accessible to voyager
            with open(DMP_MUTATIONS, 'r') as tsvfile:
                    # Initialize a list to store the matching rows
                    matching_rows = []
                    # Read the file line by line
                    for i, line in enumerate(tsvfile):
                        columns = line.strip().split('\t') 
                        line = line.strip()  # Remove leading/trailing whitespace
                
                        # If the line contains the header, add it to the matching rows
                        if i == 1:
                            matching_rows.append(line)
                        if i > 1:
                            # Check if the line matches the pattern
                            if re.match(sample, columns[16]):
                                matching_rows.append(line)
                    if len(matching_rows) > 1:
                        # impact_maf_path = self.write_to_file(f"{patient}_data_mutations.txt",'\n'.join(matching_rows))
                        impact_maf_path = write_to_file(f"{sample}_data_mutations.txt",'\n'.join(matching_rows))
                        if dmp_match_maf.get(sample) is None:
                            dmp_match_maf[sample] = [impact_maf_path]
                        else:
                            dmp_match_maf[sample].append(impact_maf_path)

        return dmp_match_maf 
    

    def write_to_file(self, fname, s):
        """
        Writes manifest csv to temporary location, registers it as tmp file
        :return: manifest csv path
        """
        # Split the string into rows using "\r\n" as the delimiter
        rows = s.split("\r\n")
        # Split each row into columns using "," as the delimiter
        data = [row.split(",") for row in rows]
        # tmp file creation
        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, fname)
        # write csv to tmp file group
        with open(output, "w+", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)
        # register output as tmp file
        self.register_temp_file(output)
        # return with juno formatting
        return {"class": "File", "location": "juno://" + output}

    @staticmethod
    def register_temp_file(output):
        os.chmod(output, 0o777)
        fname = os.path.basename(output)
        temp_file_group = FileGroup.objects.get(slug="temp")
        file_type = FileType.objects.get(name="unknown")
        f = File(file_name=fname, path=output, file_type=file_type, file_group=temp_file_group)
        f.save()
