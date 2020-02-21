import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_roslin_pair import construct_roslin_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
from pprint import pprint

class RoslinOperator(Operator):
    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__requestId=self.request_id, filemetadata__metadata__igocomplete=True).all()
        roslin_jobs = list()

        data = list()
        for file in files:
            sample = dict()
            sample['id'] = file.id
            sample['path'] = file.path
            sample['file_name'] = file.file_name
            sample['metadata'] = file.filemetadata_set.first().metadata
            data.append(sample)

        samples = list()
        # group by igoId
        igo_id_group = dict()
        for sample in data:
            igo_id = sample['metadata']['sampleId']
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        roslin_inputs, error_samples = construct_roslin_jobs(samples)
        number_of_inputs = len(roslin_inputs)

        for i, job_items in enumerate(roslin_inputs):
            job = job_items[0]
            job_metadata = job_items[1]
            tumor_sample_name = job['pair'][0]['ID']
            normal_sample_name = job['pair'][1]['ID']
            name = "ROSLIN %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            data = {
                    'app': self.get_pipeline_id(),
                    'inputs': roslin_inputs,
                    'name': name,
                    'tags': {'requestId': self.request_id},
                    'output_metadata': {
                        'assay': job_metadata['assay'],
                        'request_id': job_metadata['request_id'],
                        'tumor_igo_id': job_metadata['tumor']['igo_id'],
                        'tumor_patient_id': job_metadata['tumor']['patient_id'],
                        'normal_igo_id': job_metadata['normal']['igo_id'],
                        'normal_patient_id': job_metadata['normal']['patient_id'],
                        }
                    }
            roslin_jobs.append((APIRunCreateSerializer(data = data), job))
        return roslin_jobs
