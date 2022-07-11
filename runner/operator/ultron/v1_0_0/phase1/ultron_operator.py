"""
Ultron Operator

Constructs input JSON for the Ultron pipeline and then
submits them as runs
"""
import os
import logging
from django.conf import settings
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
        name = "ULTRON run"
        sample_groups = [self._build_sample_groups(run_ids)]
        rid = run_ids[0]  # get representative run_id from list; assumes ALL run ids use same pipeline
        input_json = dict(sample_group=sample_groups)
        ultron_output_job = list()
        ultron_output_job = self._build_job(input_json, rid)

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
            output_directory = os.path.join(
                pipeline.output_directory, "argos", project_prefix, pipeline_version, jg_created_date, "analysis"
            )
        return output_directory

    def _build_sample_groups(self, run_ids):
        sample_groups = list()
        for rid in set(run_ids):
            run = Run.objects.filter(id=rid).first()
            sample_groups.append(SampleGroup(run))
        return sample_groups

    def _build_job(self, input_json, run_id):
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = get_project_prefix(run_id)
        output_directory = self._get_output_directory(run_id)
        num_sample_groups = len(input_json)
        tags = {"project_prefix": project_prefix, "num_sample_groups": num_sample_groups}
        # add tags, name
        output_job_data = {
            "app": app,
            "tags": tags,
            "name": "Sample %s ULTRON PHASE1 run",
            "output_directory": output_directory,
            "inputs": input_json,
        }
        output_job = RunCreator(**output_job_data)
        return output_job

    def _get_prev_req_id(self, run_id):
        run = Run.objects.filter(id=run_id)[0]
        request_id = run.tags[settings.REQUEST_ID_METADATA_KEY]
        return request_id

    def _get_prev_pipeline(self, run_id):
        run = Run.objects.filter(id=run_id)[0]
        pipeline = run.app
        return pipeline


class SampleGroup:
    def __init__(self, run):
        self.run = run
        self.port_list = Port.objects.filter(run=run.id)
        self.tumor_sample_name = run.tags["sampleNameTumor"]
        self.normal_sample_name = run.tags["sampleNameNormal"]
        self.sample = self._get_samples_data()
        self.tumor_bam = self._get_port("tumor_bam")[0]
        self.normal_bam = self._get_port("normal_bam")[0]
        self.maf_file = self._get_port("maf_file")[0]
        self.maf = self._get_port("maf")[0]
        self.json = self._build_sample_group_dict()

    def _get_samples_data(self):
        files = FileRepository.all()
        f = FileRepository.filter(
            queryset=files,
            metadata={
                settings.CMO_SAMPLE_TAG_METADATA_KEY: self.tumor_sample_name,
                settings.IGO_COMPLETE_METADATA_KEY: True,
            },
            filter_redact=True,
        )
        sample = None
        if f:
            # retrieve metadata from first record (should only be one)
            meta = f[0].metadata
            sample_id = meta[settings.SAMPLE_ID_METADATA_KEY]
            sample = SampleData(sample_id, self.normal_sample_name)
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

    def _build_sample_group_dict(self):
        sample_group = list()
        json_research = self._init_research_sample_json()
        clin_jsons = self._init_clinical_samples_json()
        sample_group.append(json_research)
        for json_clin in clin_jsons:
            sample_group.append(json_clin)
        return sample_group

    def _init_research_sample_json(self):
        d = {
            "sample_id": self.tumor_sample_name,
            "normal_id": self.normal_sample_name,
            "sample_type": "research",
            "prefilter": True,
            "maf_file": {"class": "File", "path": self.maf},
            "bam_file": {"class": "File", "path": self.tumor_bam},
        }
        return d

    def _init_clinical_samples_json(self):
        clin_jsons = list()
        tumor_dmp_bams = self.sample.dmp_bams_tumor
        if tumor_dmp_bams:
            for bam_data in tumor_dmp_bams:
                d = {
                    "sample_id": bam_data.dmp_sample_name,
                    "normal_id": "DMP_NORMAL",
                    "sample_type": "clinical",
                    "prefilter": False,
                    "maf_file": {"class": "File", "path": bam_data.bam_path},
                    "bam_file": {"class": "File", "path": bam_data.mutations_extended},
                }
                clin_jsons.append(d)
        return clin_jsons

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


class SampleData:
    # Retrieves a sample's data and its corresponding DMP clinical samples
    # Limitation: tumor sample must be research sample, not clinical for now
    def __init__(self, sample_id, normal_id):
        self.files = FileRepository.all()
        self.sample_id = sample_id
        self.normal_id = normal_id  # paired normal sample name
        self.dmp_bam_file_group = get_file_group("DMP BAMs")
        self.patient_id, self.cmo_sample_name = self._get_sample_metadata()
        self.dmp_patient_id = self._get_dmp_patient_id()
        self.dmp_bams_tumor = self._find_dmp_bams("T")
        self.dmp_bams_normal = self._find_dmp_bams("N")

    def _get_sample_metadata(self):
        # gets patient id and cmo sample name from sample id query
        # condensed in this one  fucntion to reduce amount of queriesd
        files = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: self.sample_id, settings.IGO_COMPLETE_METADATA_KEY: True},
            filter_redact=True,
        )
        # there should only be one patient ID
        # looping through the metadata works here, but it's lazy
        patient_id = None
        sample_name = None
        for f in files:
            metadata = f.metadata
            if settings.PATIENT_ID_METADATA_KEY in metadata:
                pid = metadata[settings.PATIENT_ID_METADATA_KEY]
                if pid:
                    patient_id = pid
            if settings.CMO_SAMPLE_TAG_METADATA_KEY in metadata:
                sid = metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
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
            dmp_sample_name = self.metadata["sample"]
            return dmp_sample_name
        return "missingDMPSampleName"
