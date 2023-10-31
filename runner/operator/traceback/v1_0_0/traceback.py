import os
import json
import uuid
import logging
from pathlib import Path
from jinja2 import Template
from beagle import settings
from runner.operator.operator import Operator
from runner.models import RunStatus, Port, Run
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
        # CMO IMPACT mafs and bams 
        # Get IMPACT Fastqs using ACCESS Request cmoPatientId 
        # Identify IMPACT Requests that contain ACCESS Request cmoPatientId 
        impact_fastq = lims_fastq.filter(metadata__cmoPatientId__in=cmoPatientId,metadata__genePanel__regex=".*IMPACT.*")
        impact_requests = list(set([fastq.metadata["igoRequestId"] for fastq in impact_fastq]))
        # Use IMPACT Requests to get tumor_bam 
        argos_runs = []
        for request in impact_requests:
            argos_r = Run.objects.filter(app__name__regex="argos",operator_run__status=RunStatus.COMPLETED, tags__igoRequestId=request)
            if len(argos_r) == 1:
                argos_runs.append(argos_r[0].id)
            if len(argos_r) > 1:
                argos_last = argos_r.order_by('-finished_date').first()
                argos_runs.append(argos_last.id)
        impact_match_bam = {}
        #TODO CMO IMPACT NORMALS
        for run in argos_runs:
            request_bams = Port.objects.filter(name__in=["tumor_bam"], 
                                                run__id=run, 
                                                run__status=RunStatus.COMPLETED)
            
            # find which cmo patient bam this maps to and save in a dict
            for sbam in request_bams:
               sbam_cpid = re.search(r's_C_(\w{6})_',sbam.value['basename']).group(1)
               sbam_sample = re.search(r'(s_C_\w{6}_\w{4}_d\w*)\.',sbam.value['basename']).group(1)
               if sbam_cpid in cmoPatientId_trunc:
                        # self.dict_list_append(impact_match_bam,sbam_cpid, sbam)
                        if impact_match_bam.get(sbam_sample) is None:
                            impact_match_bam[sbam_sample] = [sbam.value['location']]
                        else:
                            impact_match_bam[sbam_sample].append(sbam.value['location'])
        impact_samples = list(impact_match_bam.keys())
        # Use IMPACT Requests to get MAF  
        argos_helix_ids = []
        # Mafs are in Helix filters
        for request in impact_requests:
            argos_qc_r = Run.objects.filter(app__name__regex="argos_helix_.*",operator_run__status=RunStatus.COMPLETED, tags__project_prefix=request)
            if len(argos_qc_r) == 1:
                argos_helix_ids.append(argos_qc_r[0].id)
            if len(argos_qc_r) > 1:
                argos_helix_last = argos_qc_r.order_by('-finished_date').first()
                argos_helix_ids.append(argos_helix_last.id)
        
        argos_helix_portal = Port.objects.filter(name__in=["portal_dir"],run__id__in=argos_helix_ids, run__status=RunStatus.COMPLETED)
        mut_paths = []
        for dir in argos_helix_portal:
            listing = dir.value['listing']
            for file in listing:
                if file['basename'] == 'data_mutations_extended.txt':
                    mut_paths.append(file['location'])
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
                    # impact_maf_path = write_to_file(f"{patient}_data_mutations.txt",'\n'.join(matching_rows))
                    impact_maf_path = path
                    # self.dict_list_append(impact_match_maf,pattern, impact_maf_path)
                    # dict_list_append(impact_match_maf,sample, impact_maf_path)
                    if impact_match_maf.get(sample) is None:
                        impact_match_maf[sample] = [impact_maf_path]
                    else:
                        impact_match_maf[sample].append(impact_maf_path)
        # I'd like simplify this by adding the all cmoPatientIds to the helix filter maf
        # And the cmoPatientId to each of the argos generated bams         
        # CMO ACCESS mafs and bams 
        cmo_bams = self.find_cmo_bams()
        cmo_mafs = self.find_cmo_mafs()
        # DMP mafs and bams 

        dmp_bams = FileRepository.filter(file_group=settings.DMP_BAM_FILE_GROUP)
        # subset DMP BAM file group to patients in the provided requests
        pDmps = dmp_bams.filter(metadata__patient__cmo__in=cmoPatientId_trunc)
        dmp_samples = list(pDmps.values_list('metadata__sample', flat = True))

        # subset_maf = self.read_dmp_combined_maf()

        # with open(settings.DMP_MUTATIONS, 'r') as tsvfile
        # :
        dmp_match_maf = {}
        for sample in impact_samples:
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
                            if re.match(sample, columns[15]):
                                matching_rows.append(line)
                    if len(matching_rows) > 1: 
                        # impact_maf_path = self.write_to_file(f"{patient}_data_mutations.txt",'\n'.join(matching_rows))
                        # impact_maf_path = write_to_file(f"{patient}_data_mutations.txt",'\n'.join(matching_rows))
                        impact_maf_path = path
                        # self.dict_list_append(impact_match_maf,pattern, impact_maf_path)
                        # dict_list_append(impact_match_maf,sample, impact_maf_path)
                        if dmp_match_maf.get(sample) is None:
                            dmp_match_maf[sample] = [impact_maf_path]
                        else:
                            dmp_match_maf[sample].append(impact_maf_path)

        # subset_maf = self.read_dmp_combined_maf(path)
        
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
    def find_cmo_bams(self):
        """
        creates manifest csv, write contents to file
        :return: manifest csv path
        """
        # get DMP BAM file group
        cmo_access = FileRepository.filter(file_group=settings.ACCESS_COLLAPSE_FILE_GROUP).all()
        cmo_access = FileRepository.filter(file_group="70b6484e-b45f-4007-b66e-2d47b3504111").all()
        #TODO Still start with request, but need to get all other access samples in Voyager
        cmo_access_request = cmo_access.filter(file__request_id="13893_N")
        # Need to be dynamic to tumor / or normal
        # This for tumor: simplex duplex 
        cmo_bams_request_simplex =  cmo_access_request.filter(file__file_name__regex=r".*.simplex.bam$")
        cmo_bams_request_duplex =  cmo_access_request.filter(file__file_name__regex=r".*.duplex.bam$")
        # TODO add normal bam: unfilitered bam 
        if len(cmo_bams_request_simplex) != len(cmo_bams_request_duplex):
            raise Exception("simplex and duplex bams must match for a given request.")
        cmo_duplex_bams = cmo_bams_request_duplex.values_list('file__path', flat = True)
        cmo_simplex_bams = cmo_bams_request_simplex.values_list('file__path', flat = True)
        # For a given patient -> <bams> combined_maf
        # # impact
        # patients =  File.objects.filter(file_group="40ad84eb-0694-446b-beac-59e35e154f3c", file_name__regex=".*.bam$")
        # argos =  Run.objects.filter(app="bdf41094-4c1c-11ee-b83b-ac1f6bb4ad16",operator_run__status=4)

        return cmo_duplex_bams, cmo_simplex_bams
    
    def find_cmo_mafs(self):
        cmo_access_sv = FileRepository.filter(file_group="fcec5b6e-905b-4e29-a959-f9d9e28724d3").all()
        cmo_access_svr = cmo_access_sv.filter(file__request_id="12524_D")
        cmo_mafs =  cmo_access_svr.filter(file__file_name__regex=r".*taggedHotspots_fillout_filtered.maf$")
        cmo_mafs = cmo_mafs.values_list('file__path', flat = True)
        # What to do if mafs and BAMS don't match 
        return cmo_mafs
        


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
