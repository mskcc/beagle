import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_access_data import construct_access_jobs
from .bin.make_sample import generate_results


class AccessOperator(Operator):

    def __init__(self, request_id):
        Operator.__init__(self, 'access', request_id)

    def get_pipeline_id(self):
        return "be8af61e-46f4-43d4-9838-191b17465bac" # Return ID of the pipeline

    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__requestId=self.request_id, filemetadata__metadata__igocomplete=True).all()
        access_jobs = list() #  [APIRunCreateSerializer(data={'app': self.get_pipeline_id(), 'inputs': inputs})]

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
            igo_id = sample['metadata']['igoId']
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(generate_results(igo_id_group[igo_id]))

        access_inputs = construct_access_jobs(samples)
        number_of_inputs = len(access_inputs)

        for i, job in enumerate(access_inputs):
            name = "ACCESS M1: %s, %i of %i" % (self.request_id, i + 1, number_of_inputs)
            access_jobs.append((APIRunCreateSerializer(data={'name': name,'app': self.get_pipeline_id(), 'inputs': access_inputs}), job))

        return access_jobs # Not returning anything for some reason for inputs; deal with later
