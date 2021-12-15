"""
Ultron Operator

Constructs input JSON for the Ultron pipeline and then
submits them as runs
"""
import os
import logging
from notifier.models import JobGroup
from file_system.models import FileGroup
from file_system.repository.file_repository import FileRepository
from runner.models import Pipeline, Port, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
import json

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)


def get_file_group(file_group_name):
    file_group_obj = FileGroup.objects.get(name=file_group_name)
    if not file_group_obj:
        LOGGER.error("No file group found for %s", file_group_name)
        return None
    if type(file_group_obj) == list and len(file_group_obj) > 1:
        logging.error("More than one file group returned for %s", file_group_name)
        return None
    return file_group_obj.pk


def get_project_prefix(run_id):
    project_prefix = set()
    port_list = Port.objects.filter(run=run_id)
    for single_port in port_list:
        if single_port.name == "project_prefix":
            project_prefix.add(single_port.value)
    project_prefix_str = "_".join(sorted(project_prefix))
    return project_prefix_str


class UltronOperator(Operator):
    def get_jobs(self):
        """ """
        run_ids = self.run_ids
        number_of_runs = len(run_ids)
        name = "ULTRON PHASE1 run"
        self.project_prefix = "" 

        inputs = self._build_inputs(run_ids)
        rid = run_ids[0] # get representative run_id from list; assumes ALL run ids use same pipeline
        ultron_output_job = list()
        ultron_output_job = [self._build_job(inputs, rid)]

        return ultron_output_job


    def _get_output_directory(self, run_id):
        project_prefix = get_project_prefix(run_id)
        app = self.get_pipeline_id()
        pipeline = self._get_prev_pipeline(run_id)
        pipeline_version = pipeline.version
        output_directory = None
        if self.job_group_id:
            jg = JobGroup.objects.get(id=self.job_group_id)
            jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
            output_directory = os.path.join(pipeline.output_directory,
                                            "argos",
                                            project_prefix,
                                            pipeline_version,
                                            jg_created_date,
                                            "analysis")
        return output_directory


    def _build_inputs(self, run_ids):
        input_objs = list()
        prev_pipeline_version = set()
        req_id = set()
        for rid in set(run_ids):
            run = Run.objects.filter(id=rid)[0]
            input_objs.append(InputsObj(run))
            prev_pipe = self._get_prev_pipeline(rid)
            prev_pipeline_version.add(prev_pipe.version)
            req_id.add(self._get_prev_req_id(rid))
        prev_version_string = "_".join(sorted(prev_pipeline_version))
        req_id_string = "_".join(sorted(req_id))
        batch_input_json = BatchInputObj(input_objs)
        batch_input_json.inputs_json["argos_version_string"] = prev_version_string
        batch_input_json.inputs_json["is_impact"] = True # assume True
        batch_input_json.inputs_json['fillout_output_fname'] = req_id_string + ".fillout.maf"
        return batch_input_json.inputs_json


    def _build_job(self, input_json, run_id):
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        output_directory = self._get_output_directory(run_id)
        sample_name = input_json["sample_ids"]
        tags = {"sampleNameTumor": sample_name, "project_prefix": self.project_prefix}
        # add tags, name
        output_job_data = {
            "app": app,
            "tags": tags,
            "name": "Sample %s ULTRON PHASE1 run" % sample_name,
            "output_directory": output_directory,
            "inputs": input_json,
        }
        output_job = RunCreator(**output_job_data)
        return output_job


    def _get_prev_req_id(self, run_id):
        run = Run.objects.filter(id=run_id)[0]
        request_id = run.tags['requestId']
        return request_id


    def _get_prev_pipeline(self, run_id):
        run = Run.objects.filter(id=run_id)[0]
        pipeline = run.app
        return pipeline


class BatchInputObj:
    def __init__(self, inputObjList):
        self.inputObjList = inputObjList
        self.inputs_json = self._build_inputs_json()

    def _build_inputs_json(self):
        batch_input_json = {
            "unindexed_bam_files": [],
            "unindexed_sample_ids": [],
            "unindexed_maf_files": [],
            "maf_files": [],
            "bam_files": [],
            "sample_ids": [],
            "ref_fasta": None,
            "exac_filter": None,
        }
        for single_input_obj in self.inputObjList:
            single_input_data = single_input_obj.inputs_data
            if single_input_data["tumor_sample_name"] not in batch_input_json["sample_ids"]:
                batch_input_json["maf_files"] += single_input_data["maf"]
                batch_input_json["bam_files"] += single_input_data["tumor_bam"]
                batch_input_json["sample_ids"] += single_input_data["tumor_sample_name"]
                if not batch_input_json["ref_fasta"]:
                    batch_input_json["ref_fasta"] = single_input_obj.load_reference_fasta()
                if not batch_input_json["exac_filter"]:
                    batch_input_json["exac_filter"] = single_input_obj.load_exac_filter()
                # dedupe dmp samples
                dmp_tumor_sample_names = single_input_data["dmp_bams_tumor_sample_name"]
                for i in dmp_tumor_sample_names:
                    if i not in batch_input_json["unindexed_sample_ids"]:
                        batch_input_json["unindexed_bam_files"] += single_input_data["dmp_bams_tumor"]
                        batch_input_json["unindexed_sample_ids"] += single_input_data["dmp_bams_tumor_sample_name"]
                        batch_input_json["unindexed_maf_files"] += single_input_data["dmp_bams_tumor_muts"]
        return batch_input_json


class InputsObj:
    # This inputs object will represent the input json used for the pipeline
    #
    # There should only be a single tumor sample, mathced against DMP bam tumors
    # provided they exist
    def __init__(self, run):
        self.run = run
        self.port_list = Port.objects.filter(run=run.id)
        self.tumor_sample_name = run.tags["sampleNameTumor"]
        self.sample = self._get_samples_data()
        self.tumor_bam = self._get_port("tumor_bam")
        self.normal_bam = self._get_port("normal_bam")
        self.normal_sample_name = run.tags["sampleNameNormal"]
        self.maf_file = self._get_port("maf_file")
        self.maf = self._get_port("maf")
        self.inputs_data = self._set_inputs_data()
        self.inputs_json = self._build_inputs_json()

    def _get_samples_data(self):
        files = FileRepository.all()
        f = FileRepository.filter(
            queryset=files, metadata={"cmoSampleName": self.tumor_sample_name, "igocomplete": True}, filter_redact=True
        )
        sample = None
        if f:
            # retrieve metadata from first record (should only be one)
            meta = f[0].metadata
            sample_id = meta["sampleId"]
            sample = SampleData(sample_id)
        return sample

    def _get_port(self, port_name):
        for single_port in self.port_list:
            current_port = single_port.name
            if current_port == port_name:
                return self._get_files_from_port(single_port.value)
        return None

    def _get_files_from_port(self, port_obj):
        file_list = []
        if isinstance(port_obj, list):
            for single_file in port_obj:
                file_list.append(self._get_file_obj(single_file))
        elif isinstance(port_obj, dict):
            file_list.append(self._get_file_obj(port_obj))
        return file_list

    def _get_file_obj(self, file_obj):
        """
        Given file_obj, construct a dictionary of class File, that file's
        JUNO-specific URI file path, and a list of secondary files with
        JUNO-specific URI file paths
        """
        secondary_file_list = []
        file_location = file_obj["location"].replace("file://", "")
        if "secondaryFiles" in file_obj:
            for single_secondary_file in file_obj["secondaryFiles"]:
                secondary_file_location = single_secondary_file["location"].replace("file://", "")
                secondary_file_cwl_obj = self._create_cwl_file_obj(secondary_file_location)
                secondary_file_list.append(secondary_file_cwl_obj)
        file_cwl_obj = self._create_cwl_file_obj(file_location)
        if secondary_file_list:
            file_cwl_obj["secondaryFiles"] = secondary_file_list
        return file_cwl_obj

    def _create_cwl_file_obj(self, file_path):
        cwl_file_obj = {"class": "File", "location": "juno://%s" % file_path}
        return cwl_file_obj

    def _set_inputs_data(self):
        sample = self.sample
        inputs_data = dict()
        inputs_data["tumor_bam"] = self.tumor_bam
        inputs_data["normal_bam"] = self.normal_bam
        inputs_data["maf"] = self.maf
        inputs_data["dmp_bams_tumor"] = list()
        inputs_data["dmp_bams_tumor_muts"] = list()
        inputs_data["dmp_bams_tumor_sample_name"] = list()
        inputs_data["tumor_sample_name"] = list()
        inputs_data["tumor_sample_name"].append(sample.cmo_sample_name)
        if sample.dmp_bams_tumor:
            for f in sample.dmp_bams_tumor:
                inputs_data["dmp_bams_tumor"].append(self._create_cwl_file_obj(f.bam_path))
                inputs_data["dmp_bams_tumor_sample_name"].append(f.dmp_sample_name)
                if f.mutations_extended:
                    inputs_data["dmp_bams_tumor_muts"].append(self._create_cwl_file_obj(f.mutations_extended))
        return inputs_data

    def _build_inputs_json(self):
        inputs_json = dict()
        inputs_json["unindexed_bam_files"] = self.inputs_data["dmp_bams_tumor"]
        inputs_json["unindexed_sample_ids"] = self.inputs_data["dmp_bams_tumor_sample_name"]
        inputs_json["unindexed_maf_files"] = self.inputs_data["dmp_bams_tumor_muts"]
        inputs_json["maf_files"] = self.inputs_data["maf"]
        inputs_json["bam_files"] = self.inputs_data["tumor_bam"]
        inputs_json["sample_ids"] = self.inputs_data["tumor_sample_name"]
        inputs_json["ref_fasta"] = self.load_reference_fasta()
        inputs_json["exac_filter"] = self.load_exac_filter()
        return inputs_json

    def load_reference_fasta(self):
        ref_fasta_path = json.load(open(os.path.join(WORKDIR, "reference_json/genomic_resources.json"), "rb"))
        ref_fasta = {"class": "File", "location": str(ref_fasta_path["ref_fasta"])}
        return ref_fasta

    def load_exac_filter(self):
        exac_filter_path = json.load(open(os.path.join(WORKDIR, "reference_json/genomic_resources.json"), "rb"))
        exac_filter = {"class": "File", "location": str(exac_filter_path["exac_filter"])}
        return exac_filter


class SampleData:
    # Retrieves a sample's data and its corresponding DMP clinical samples
    # Limitation: tumor sample must be research sample, not clinical for now
    def __init__(self, sample_id):
        self.files = FileRepository.all()
        self.sample_id = sample_id
        self.dmp_bam_file_group = get_file_group("DMP BAMs")
        self.patient_id, self.cmo_sample_name = self._get_sample_metadata()
        self.dmp_patient_id = self._get_dmp_patient_id()
        self.dmp_bams_tumor = self._find_dmp_bams("T")
        self.dmp_bams_normal = self._find_dmp_bams("N")

    def _get_sample_metadata(self):
        # gets patient id and cmo sample name from sample id query
        # condensed in this one  fucntion to reduce amount of queriesd
        files = FileRepository.filter(metadata={"sampleId": self.sample_id, "igocomplete": True}, filter_redact=True)
        # there should only be one patient ID
        # looping through the metadata works here, but it's lazy
        patient_id = None
        sample_name = None
        for f in files:
            metadata = f.metadata
            if "patientId" in metadata:
                pid = metadata["patientId"]
                if pid:
                    patient_id = pid
            if "cmoSampleName" in metadata:
                sid = metadata["cmoSampleName"]
                if sid:
                    sample_name = sid
        return patient_id, sample_name

    def _get_dmp_patient_id(self):
        # Remove C- prefix to match DMP patient ID format
        if self.patient_id:
            return self.patient_id.lstrip("C-")
        return None

    def _find_dmp_bams(self, tumor_type):
        # Retrieves dmp samples based on dmp bams
        file_list = list()
        if self.dmp_patient_id:
            files = FileRepository.filter(
                queryset=self.files,
                file_group=self.dmp_bam_file_group,
                metadata={"patient__cmo": self.dmp_patient_id, "type": tumor_type},
            )
            if files:
                for f in files:
                    file_list.append(BamData(f))
                return file_list
        return None

    def __str__(self):
        return (
            "Sample ID: %s ; Patient ID: %s ;\
                DMP Patient ID: %s"
            % (self.sample_id, self.patient_id, self.dmp_patient_id)
        )
        return results


class BamData:
    def __init__(self, dmp_file):
        self.files = FileRepository.all()
        self.dmp_file = dmp_file
        self.bam_path = dmp_file.file.path
        self.metadata = dmp_file.metadata
        self.mutations_extended_file_group = get_file_group("DMP Data Mutations Extended")
        self.mutations_extended = self._set_data_muts_txt()
        self.dmp_sample_name = self._set_dmp_sample_name()

    def _set_data_muts_txt(self):
        results = self._get_muts()
        return results

    def _get_muts(self):
        # There should only be one mutations file returned here, one per dmp sample
        query_results = FileRepository.filter(
            queryset=self.files,
            file_group=self.mutations_extended_file_group,
            metadata={"sample": self.metadata["sample"]},
        )
        results = list()
        if query_results:
            for item in query_results:
                results.append(item.file.path)
        if len(results) > 1:
            LOGGER.error("More than one mutations file found for %s", self.metadata["sample"])
        if results:
            return results[0]
        return results

    def _set_dmp_sample_name(self):
        if "sample" in self.metadata:
            dmp_sample_name = self.metadata['sample']
            return dmp_sample_name
        return "missingDMPSampleName"
