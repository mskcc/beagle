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
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        self.OUTPUT_DIR = pipeline.output_directory
        # get request id
        self.request_ids = get_request_id(self.run_ids, self.request_id)
        # get fastq metadata for a given request
        lims_fastq = FileRepository.filter(file_group=settings.LIMS_FILE_GROUP)
        access_fastq = lims_fastq.filter(file__request_id=self.request_ids)
        cmoPatientId = list(set(access_fastq.values_list('metadata__cmoPatientId', flat = True)))
        cmoPatientId_trunc = [patient.strip('C-') for patient in cmoPatientId]

        # CMO ACCESS BAMS and MAFs 
        cmo_bams_xs_tumor, cmo_bams_xs_normal = self.find_cmo_xs_bams(cmoPatientId)
        cmo_xs_mafs = self.find_cmo_xs_mafs(cmoPatientId)
        # record those bams missing mafs
        cmo_xs_missing_maf = list(set(cmo_bams_xs_tumor.keys()) - set(cmo_xs_mafs.keys()))

        # CMO IMPACT BAMS and MAFs
        cmo_bams_imp_tumor, cmo_bams_imp_normal = self.find_cmo_imp_bams(cmoPatientId, cmoPatientId_trunc)
        cmo_mafs_imp = self.find_cmo_imp_mafs(cmoPatientId, cmoPatientId_trunc)
        impact_samples_tumor = list(cmo_bams_imp_tumor.keys())
        cmo_imp_mafs = self.subset_helix_maf(impact_samples_tumor, cmo_mafs_imp)
        # record those bams missing mafs
        cmo_imp_missing_maf = list(set(cmo_bams_imp_tumor.keys()) - set(cmo_imp_mafs.keys()))


        # DMP BAMS and MAFS (IMPACT AND XS)
        dmp_bams_tumor_imp, dmp_bams_tumor_xs, dmp_bams_normal = self.find_dmp_bams(cmoPatientId_trunc)
        dmp_samples_tumor = list(dmp_bams_tumor_imp.keys()) + list(dmp_bams_tumor_xs)
        dmp_mafs = self.subset_dmp_maf(dmp_samples_tumor)
        cmo_imp_missing_maf = list(set(dmp_samples_tumor) - set(dmp_mafs.keys()))

        bams_missing_mafs = cmo_imp_missing_maf + cmo_imp_missing_maf + cmo_xs_missing_maf
        
        mafs = {**cmo_imp_mafs, **dmp_mafs,**cmo_xs_mafs}
        standard_bams = {**dmp_bams_tumor_imp,**dmp_bams_tumor_imp,**cmo_bams_imp_normal, **cmo_bams_xs_normal,**dmp_bams_normal}
        xs_bams = {**cmo_bams_xs_tumor,**dmp_bams_tumor_xs}
        self.write_sample_sheet(standard_bams, ['sample','standard'], 'standard_bams.tsv', '\t')
        self.write_sample_sheet(xs_bams, ['sample','simplex','duplex'], 'xs_bams.tsv', '\t')
        self.write_sample_sheet(mafs, ['sample','maf'], 'mafs.tsv', '\t')
        
        # TODO finish traceback pipeline and construct input 
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

    def write_sample_sheet_test(data, header, fname, sep):
        output = os.path.join("/home/buehlere/voyager_test/traceback", fname)
        with open(output, 'w') as file:
            # Write the header
            line = f'{sep}'.join(header)
            file.write(f"{line}\n")
            # Write the data
            for key, values in data.items():
                values = [value.replace("file://", "") for value in values]
                paths = sep.join(map(str, values))
                line = f"{key}{sep}{paths}\n"
                file.write(line)
        os.chmod(output, 0o777)
        # self.register_tmp_file(output, "traceback_sample_sheets")
        return output

    def write_sample_sheet(self, data, header, fname):
        output = os.path.join(self.OUTPUT_DIR, fname)
        with open(output, 'w') as file:
            # Write the header
            line = f'{sep}'.join(header)
            file.write(f"{line}\n")
            # Write the data
            for key, values in data.items():
                values = [value.replace("file://", "") for value in values]
                paths = sep.join(map(str, values))
                line = f"{key}{sep}{paths}\n"
                file.write(line)
        os.chmod(output, 0o777)
        self.register_tmp_file(output, "traceback_sample_sheets")
        return output

    def find_dmp_bams(self, cmoPatientId_trunc):
        dmp_bams = FileRepository.filter(file_group=settings.DMP_BAM_FILE_GROUP)
        # subset DMP BAM file group to patients in the provided requests
        pDmpsTumor = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trunc, metadata__type='T')
        pDmpsNormal = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trunc, metadata__type='N')
        pDmpsTumorBamImp =  {}
        pDmpsTumorBamXs =  {}
        for r in pDmpsTumor:
            if "XS" in r.metadata["sample"]:
                pDmpsTumorBamXs[r.metadata["sample"]] = [r.file.path.replace("standard","simplex"), r.file.path.replace("standard","duplex")]
            else:
                pDmpsTumorBamImp[r.metadata["sample"]] =  [r.file.path]
        pDmpsNormalBam = {r.metadata["sample"]: [r.file.path] for r in pDmpsNormal}
        return pDmpsTumorBamImp, pDmpsTumorBamXs, pDmpsNormalBam
    

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

    def write_to_file_maf(self, fname, s):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = os.path.join(self.OUTPUT_DIR, fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        self.register_tmp_file(output, "subset_mafs_traceback")
        return output
    
    def write_to_file_test(fname, s):
        """
        Writes file to temporary location, then registers it to the temp file group
        Also uploads it to notifier if there is a job group id
        """
        output = os.path.join("/home/buehlere/voyager_test", fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        return output

    def register_tmp_file(self, path, slug):
        fname = os.path.basename(path)
        temp_file_group = FileGroup.objects.get(slug=slug)
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
        xs_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
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
        xs_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*ACCESS.*")
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
        impact_fastqs= self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*IMPACT.*")
        impact_fastq_tumor = impact_fastqs.filter(metadata__tumorOrNormal="Tumor")
        impact_fastq_norm = impact_fastqs.filter(metadata__tumorOrNormal="Normal")
        impact_requests = list(set([fastq.metadata["igoRequestId"] for fastq in impact_fastqs]))
        impact_samples_tumor = list(set([fastq.metadata["cmoSampleName"] for fastq in impact_fastq_tumor]))
        impact_runs_maf = self.find_recent_runs_helix(impact_requests, "HelixFiltersOperator*")
        impact_mafs = self.find_run_files_helix(impact_runs_maf, ['portal_dir'])
        return impact_mafs
    
    def find_cmo_imp_bams(self, cmoPatientId, cmoPatientId_trunc):
        impact_fastq = self.lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*IMPACT.*")
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
                # sample should be in our list of patients
                # and we shouldn't have seen this sample in another run (normals can be re-used)
                if bool(pids.intersection(patient)):
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
                        file_match[sbam_sample] = [file_location]
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
    
    def subset_helix_maf(self, impact_samples, mut_paths):
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
                    impact_maf_path = self.write_to_file_maf(f"{sample}_data_mutations.txt",'\n'.join(matching_rows))
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
    
    def subset_dmp_maf(self, dmp_samples):
        dmp_match_maf = {}
        for sample in dmp_samples:
            # with open(settings.DMP_MUTATIONS, 'r') as tsvfile:
            with open(settings.DMP_MUTATIONS, 'r') as tsvfile:
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
                        impact_maf_path = self.write_to_file_maf(f"{sample}_data_mutations.txt",'\n'.join(matching_rows))
                        if dmp_match_maf.get(sample) is None:
                            dmp_match_maf[sample] = [impact_maf_path]
                        else:
                            dmp_match_maf[sample].append(impact_maf_path)

        return dmp_match_maf 
    
