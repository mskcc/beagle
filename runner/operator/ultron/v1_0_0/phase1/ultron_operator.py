"""
Ultron Operator

Constructs input JSON for the Ultron pipeline and then
submits them as runs
"""
import os
import datetime
import logging
from notifier.models import JobGroup
from runner.models import Port, Run
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from file_system.repository.file_repository import FileRepository
import json
WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)


class UltronOperator(Operator):
    def get_jobs(self):
        """
        """
        run_ids = self.run_ids
        number_of_runs = len(run_ids)
        name = "ULTRON PHASE1 run"

        inputs = self._build_inputs(run_ids)

        ultron_output_jobs = list()
        for input_json in inputs:
            output_job = self._build_job(input_json)
            ultron_output_jobs.append(output_job)

        return ultron_output_jobs


    def _build_inputs(self, run_ids):
        run_jsons = list() 
        for rid in set(run_ids):
            run = Run.objects.filter(id=rid)[0]
            inputs_data = InputsObj(run)
            run_jsons.append(inputs_data.inputs_json)
        return run_jsons


    def _build_job(self, input_json):
#        app = self.get_pipeline_id()
        app = "d9c8606b-f596-43b8-9cfc-5d83af4edf2d" # reassign this
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        # add tags, name
        output_job_data = {
            'app': app,
            'inputs': input_json}
        output_job = (APIRunCreateSerializer(
            data=output_job_data),
            input_json)
        return output_job


class InputsObj:
    def __init__(self, run):
        self.run = run
        self.port_list = Port.objects.filter(run = run.id)
        self.samples = self._get_samples_data()
        self.tumor_bam = self._get_port("tumor_bam")
        self.tumor_sample_name = run.tags['sampleNameTumor']
        self.normal_bam = self._get_port("normal_bam")
        self.normal_sample_name = run.tags['sampleNameNormal']
        self.maf_file = self._get_port("maf_file")
        self.maf = self._get_port("maf")
        self.inputs_data = self._set_inputs_data()
        self.inputs_json = self._build_inputs_json()


    def _get_samples_data(self):
        samples = list()
        for sample in self.run.samples.all():
            samples.append(SampleData(sample.sample_id))
        return samples


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
        file_list = []
        secondary_file_list = []
        file_location = file_obj['location'].replace('file://', '')
        file_cwl_obj = self._create_cwl_file_obj(file_location)
        file_list.append(file_cwl_obj)
        if 'secondaryFiles' in file_obj:
            for single_secondary_file in file_obj['secondaryFiles']:
                secondary_file_location = single_secondary_file['location'].replace(
                    'file://', '')
                secondary_file_cwl_obj = self._create_cwl_file_obj(
                    secondary_file_location)
                secondary_file_list.append(secondary_file_cwl_obj)
        return {'files': file_list, 'secondary_files': secondary_file_list}


    def _create_cwl_file_obj(self, file_path):
        cwl_file_obj = {'class': 'File', 'location': "juno://%s" % file_path}
        return cwl_file_obj


    def _set_inputs_data(self):
        inputs_data = dict()
        inputs_data['tumor_bam'] = self.tumor_bam
        inputs_data['normal_bam'] = self.normal_bam
        inputs_data['maf'] = self.maf
        inputs_data['dmp_bams_tumor'] = list()
        inputs_data['dmp_bams_tumor_muts'] = list()
        inputs_data['dmp_bams_tumor_sample_name'] = list()
        inputs_data['tumor_sample_name'] = list()
        for sample in self.samples:
            inputs_data['tumor_sample_name'].append(sample.cmo_sample_name)
            if sample.dmp_bams_tumor:
                for f in sample.dmp_bams_tumor:
                    inputs_data['dmp_bams_tumor'].append(self._create_cwl_file_obj(f.bam_path))
                    inputs_data['dmp_bams_tumor_sample_name'].append(f.dmp_sample_name)
                    if f.mutations_extended:
                        inputs_data['dmp_bams_tumor_muts'].append(self._create_cwl_file_obj(f.mutations_extended))
        return inputs_data


    def _build_inputs_json(self):
        inputs_json = dict()
        inputs_json['dmp_bams'] = self.inputs_data['dmp_bams_tumor']
        inputs_json['dmp_bams_sample_names'] = self.inputs_data['dmp_bams_tumor_sample_name']
        inputs_json['dmp_maf_files'] = self.inputs_data['dmp_bams_tumor_muts']
        inputs_json['maf_files'] = self.inputs_data['maf']
        inputs_json['bam_files'] = self.inputs_data['tumor_bam']
        inputs_json['sample_names'] = self.inputs_data['tumor_sample_name']
        inputs_json['ref_fasta'] = self.load_reference_fasta()
        return inputs_json


    def load_reference_fasta(self):
        ref_fasta_path = json.load(open(os.path.join(WORKDIR, "reference_json/genomic_resources.json"), 'rb'))
        ref_fasta = { "ref_fasta": {"class": "File", "location": str(ref_fasta_path['ref_fasta']) }}
        return ref_fasta


class SampleData:
    # Retrieves a sample's data and its corresponding DMP clinical samples
    # Limitation: tumor sample must be research sample, not clinical for now
    def __init__(self, sample_id):
        self.files = FileRepository.all()
        self.sample_id = sample_id
        self.patient_id, self.cmo_sample_name = self._get_sample_metadata()
        self.dmp_patient_id = self._get_dmp_patient_id()
        self.dmp_bams_tumor = self._find_dmp_bams("T")
        self.dmp_bams_normal = self._find_dmp_bams("N")

    def _get_sample_metadata(self):
        # gets patient id and cmo sample name from sample id query
        # condensed in this one  fucntion to reduce amount of queriesd
        files = FileRepository.filter(queryset=self.files,
                metadata={'sampleId': self.sample_id,
                    'igocomplete': True},
                filter_redact=True)
        # there should only be one patient ID
        # looping through the metadata works here, but it's lazy
        patient_id = None
        sample_name = None
        for f in files:
            metadata = f.metadata
            if 'patientId' in metadata:
                pid = metadata['patientId']
                if pid:
                    patient_id = pid
            if 'cmoSampleName' in metadata:
                sid = metadata['cmoSampleName']
                if sid:
                    sample_name = sid
        return patient_id, sample_name


    def _get_dmp_patient_id(self):
        # Remove C- prefix to match DMP patient ID format
        if self.patient_id:
            return self.patient_id.lstrip('C-')
        return None

    def _find_dmp_bams(self, tumor_type):
        # Retrieves dmp samples based on dmp bams
        file_list = list()
        if self.dmp_patient_id:
            files = FileRepository.filter(queryset=self.files,
                    metadata={'patient__cmo': self.dmp_patient_id, "type": tumor_type})
            if files:
                for f in files:
                    file_list.append(BamData(f))
                return file_list
        return None

    def __str__(self):
        return "Sample ID: %s ; Patient ID: %s ;\
                DMP Patient ID: %s" % (self.sample_id,
                        self.patient_id, self.dmp_patient_id)


class BamData:
    def __init__(self, voyager_file):
        self.files = FileRepository.all()
        self.voyager_file = voyager_file
        self.bam_path = voyager_file.file.path
        self.metadata = voyager_file.metadata
        self.mutations_extended = self._set_data_muts_txt()
        self.dmp_sample_name = self._set_dmp_sample_name()

    def _set_data_muts_txt(self):
        meta = self.metadata
        external_id = None
        investigator_sample_id = None
        dmp_key = "sample"
        results = self._get_muts(dmp_key, meta)
        if results:
            return results
        return None

    def _get_muts(self, key, meta):
        # There should only be one mutations file returned here, one per dmp sample
        data_id = meta[key]
        query_results = FileRepository.filter(queryset=self.files, metadata={'dmp_link_id':data_id})
        results = list()
        if query_results:
            for item in query_results:
                results.append(item.file.path)
        if len(results) > 1:
            LOGGER.error("More than one mutations file found for %s", data_id)
        if results:
            return results[0]
        return results

    def _set_dmp_sample_name(self):
        if 'external_id' in self.metadata:
            dmp_sample_name = self.metadata['external_id']
            if "s_" not in dmp_sample_name[:2]:
                dmp_sample_name = "s_" + dmp_sample_name.replace("-", "_")
            return dmp_sample_name
        return None
