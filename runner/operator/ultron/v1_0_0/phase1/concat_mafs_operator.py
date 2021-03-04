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


class ConcatMafsOperator(Operator):
    def get_jobs(self):
        """
        """
        run_ids = self.run_ids
        number_of_runs = len(run_ids)
        name = "ULTRON PHASE1 run, CONCAT MAFs"
        inputs = self._build_inputs(run_ids)
        inputs_json = inputs.inputs_json
        ultron_output_job = self._build_job(inputs_json)
        return ultron_output_job


    def _build_inputs(self, run_ids):
        inputs_json = InputsObj(run_ids)
        return inputs_json


    def _build_job(self, input_json):
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        request_id = self._get_request_id()
        input_json['output_filename'] = request_id + ".rez.maf"
        tags = {'requestId': request_id}
        # add tags, name
        output_job_data = {
            'app': app,
            'tags': tags,
            'name': "Request ID %s ULTRON PHASE1:CONCAT MAFs run" % request_id,
            'inputs': input_json}
        output_job = (APIRunCreateSerializer(
            data=output_job_data),
            input_json)
        return output_job


    def _get_request_id(self):
        files = FileRepository.all()
        request_ids = set()
        for run_id in self.run_ids:
            run = Run.objects.filter(id=run_id)[0]
            sample_name = run.tags['sampleNameTumor']
            sample_files = FileRepository.filter(queryset=files, metadata = {'cmoSampleName': sample_name})
            for f in sample_files:
                metadata = f.metadata
                if 'requestId' in metadata:
                    request_ids.add(metadata['requestId'])
        request_id = "_".join(list(request_ids))
        return request_id


class InputsObj:
    def __init__(self, run_ids):
        self.run_ids = run_ids
        self.mafs = self._get_mafs()
        self.inputs_json = self._build_inputs_json()


    def _get_mafs(self):
        mafs = list()
        for run_id in self.run_ids:
            port_list = Port.objects.filter(run = run_id)
            maf_files = self._get_port(port_list, "output_file")
            for maf in maf_files:
                mafs.append(maf)
        return mafs


    def _get_port(self, port_list, port_name):
        for single_port in port_list:
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


    def _get_file_obj(self,file_obj):
        """
        Given file_obj, construct a dictionary of class File, that file's
        JUNO-specific URI file path, and a list of secondary files with
        JUNO-specific URI file paths
        """
        secondary_file_list = []
        file_location = file_obj['location'].replace('file://', '')
        if 'secondaryFiles' in file_obj:
            for single_secondary_file in file_obj['secondaryFiles']:
                secondary_file_location = single_secondary_file['location'].replace(
                    'file://', '')
                secondary_file_cwl_obj = self._create_cwl_file_obj(
                    secondary_file_location)
                secondary_file_list.append(secondary_file_cwl_obj)
        file_cwl_obj = self._create_cwl_file_obj(file_location)
        if secondary_file_list:
            file_cwl_obj['secondaryFiles'] = secondary_file_list
        return file_cwl_obj


    def _create_cwl_file_obj(self, file_path):
        cwl_file_obj = {'class': 'File', 'location': "juno://%s" % file_path}
        return cwl_file_obj


    def _build_inputs_json(self):
        inputs_json = dict()
        inputs_json['input_files'] = self.mafs
        return inputs_json
