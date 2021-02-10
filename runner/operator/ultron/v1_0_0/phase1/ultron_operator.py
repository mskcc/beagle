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

        return ultron_outputs_jobs


    def _build_inputs(self, run_ids):
        run_jsons = list() 
#        for rid in set(run_ids):
#            run = Run.objects.filter(id=rid)[0]
#            run_jsons[rid] = RunPatients(rid)
#            samples = run.samples.all()
#            for sample in samples:
#                patients = self._get_patient_from_sample(sample.sample_id)
#                for p in patients:
#                    run_jsons[rid].add_patient(p)
        return run_jsons


    def _build_job(self, input_json):
#        app = self.get_pipeline_id()
#        pipeline = Pipeline.objects.get(id=app)
#        pipeline_version = pipeline.version
        app = "test_pipeline_app_id"


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
        self.normal_bam = self._get_port("normal_bam")
        self.maf_file = self._get_port("maf_file")
        self.maf = self._get_port("maf")
        self.inputs_json = self._set_inputs_json()


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


    def _set_inputs_json(self):
        inputs_json = dict()
        inputs_json['tumor_bam'] = self.tumor_bam
        inputs_json['normal_bam'] = self.normal_bam
        inputs_json['maf_file'] = self.maf_file
        inputs_json['maf'] = self.maf
        inputs_json['dmp_bams_tumor'] = list()
        inputs_json['dmp_bams_normal'] = list()
        for sample in self.samples:
            if sample.dmp_bams_tumor:
                for f in sample.dmp_bams_tumor:
                    inputs_json['dmp_bams_tumor'].append(self._create_cwl_file_obj(f))
            if sample.dmp_bams_normal:
                for f in sample.dmp_bams_normal:
                    inputs_json['dmp_bams_normal'].append(self._create_cwl_file_obj(f))
        return inputs_json


class SampleData:
    def __init__(self, sample_id):
        self.files = FileRepository.all()
        self.sample_id = sample_id
        self.patient_id = self._get_patient_id()
        self.dmp_patient_id = self._get_dmp_patient_id()
        self.dmp_bams_tumor = self._find_dmp_bams("T")
        self.dmp_bams_normal = self._find_dmp_bams("N")

    def _get_patient_id(self):
        files = FileRepository.filter(queryset=self.files,
                metadata={'sampleId': self.sample_id,
                    'igocomplete': True},
                filter_redact=True)
        # there should only be one patient ID
        for f in files:
            metadata = f.metadata
            if 'patientId' in metadata:
                patient_id = metadata['patientId']
                if patient_id:
                    return patient_id
        return None

    def _get_dmp_patient_id(self):
        # Remove C- prefix to match DMP patient ID format
        if self.patient_id:
            return self.patient_id.lstrip('C-')

    def _find_dmp_bams(self, tumor_type):
        # Retrieves dmp samples based on dmp bams
        file_list = list()
        if self.dmp_patient_id:
            files = FileRepository.filter(queryset=self.files,
                    metadata={'patient__cmo': self.dmp_patient_id, "type": tumor_type})
            if files:
                for f in files:
                    file_list.append(f.file.path)
                return file_list
        return None

    def __str__(self):
        return "Sample ID: %s ; Patient ID: %s ;\
                DMP Patient ID: %s" % (self.sample_id,
                        self.patient_id, self.dmp_patient_id)
