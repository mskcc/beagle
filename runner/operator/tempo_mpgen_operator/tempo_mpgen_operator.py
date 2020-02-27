import uuid
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from .construct_tempo_pair import construct_tempo_jobs
from .bin.pair_request import compile_pairs
from .bin.make_sample import build_sample
import json

class TempoMPGenOperator(Operator):
    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__requestId=self.request_id, filemetadata__metadata__igocomplete=True).all()
        tempo_jobs = list()

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
        sample_id_group = dict()
        for sample in data:
            sample_id = sample['metadata']['sampleId']
            if sample_id not in sample_id_group:
                sample_id_group[sample_id] = list()
            sample_id_group[sample_id].append(sample)

        for sample_id in sample_id_group:
            samples.append(build_sample(sample_id_group[sample_id]))

        tempo_inputs, error_samples = construct_tempo_jobs(samples)
        number_of_inputs = len(tempo_inputs)

        f = open("/home/bolipatc/ops/test_tempo/%s.json" % (self.request_id), 'w')
        json.dump(tempo_inputs, f)

        return tempo_jobs
