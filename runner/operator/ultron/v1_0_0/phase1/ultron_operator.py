"""
Ultron Operator

Constructs input JSON for the Ultron pipeline and then
submits them as runs
"""
import os
import datetime
import logging
from notifier.models import JobGroup
from runner.models import Run
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
        name = "ULTRON" % (
            number_of_runs, lab_head_email)

        inputs = self._build_inputs(run_ids)

        ultron_output_jobs = list()
        for input_json in inputs:
            output_job = self._build_job(input_json)
            ultron_output_jobs.append(output_job)

        return ultron_outputs_jobs


    def _build_inputs(self, run_ids):
        run_jsons = dict()
        for rid in run_ids:
            run = Run.objects.filter(id=rid)[0]
            run_jsons[rid] = RunPatients(rid)
            samples = run.samples.all()
            for sample in samples:
                patients = self._get_patient_from_sample(sample.sample_id)
                for p in patients:
                    run_jsons[rid].add_patient(p)
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


    def _get_patient_from_sample(self, sample_id):
        files = FileRepository.filter(queryset=self.files,
                metadata={'sampleId': sample_id,
                    'igocomplete': True},
                filter_redact=True)
        patient = set()
        for f in files:
            metadata = f.metadata
            if 'patientId' in metadata:
                patient_id = metadata['patientId']
                if patient_id:
                    patient.add(patient_id)
        return patient


class RunPatients:
    def __init__(self, run_id):
        self.run_id = run_id
        self.patients = set()


    def add_patient(self, patient_id):
        self.patients.add(patient_id)
