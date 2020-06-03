import re
from django.db.models import Q
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
import runner.operator.tempo_mpgen_operator.bin.tempo_sample as tempo_sample


class Patient:
    def __init__(self, patient_id, file_list):
        self.samples = self._get_samples(file_list)

    def _get_samples(self, file_list):
        data = dict()
        for f in file_list:
            metadata = f.metadata
            sample_name = metadata['sampleName']
            if sample_name not in data:
                data[sample_name] = list()
            data[sample_name].append(f)

        samples = dict()
        for sample_id in data:
            samples[sample_id] = tempo_sample.TempoSample(sample_id, data[sample_id])
        return samples
