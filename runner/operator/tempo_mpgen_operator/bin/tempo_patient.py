import re
from datetime import datetime as dt
from django.db.models import Q
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
import runner.operator.tempo_mpgen_operator.bin.tempo_sample as tempo_sample


class Patient:
    def __init__(self, patient_id, file_list):
        self.tumor_samples = dict()
        self.normal_samples = dict()
        self.conflict_samples = dict()
        self.sample_pairing = list()
        self.unpaired_samples = list()
        self._samples = self._get_samples(file_list)
        self._characterize_samples()
        self._pair_samples()

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
            sample = data[sample_id]
            samples[sample_id] = tempo_sample.TempoSample(sample_id, sample)
        return samples

    def _characterize_samples(self):
        for sample_id in self._samples:
            sample = self._samples[sample_id]
            sample_class = sample.sample_class
            if not sample_class:
                self.conflict_samples[sample_id] = sample
            elif isinstance(sample_class, list):
                self.conflict_samples[sample_id] = sample
            else:
                if "normal" in sample_class.lower():
                    self.normal_samples[sample_id] = sample
                else:
                    self.tumor_samples[sample_id] = sample

    def _pair_samples(self):
        for tumor_sample_id in self.tumor_samples:
            tumor_sample = self.tumor_samples[tumor_sample_id]
            tumor_baits = tumor_sample.bait_set
            normal = self._get_normal(tumor_baits)
            if normal:
                self.sample_pairing.append([tumor_sample, normal])
            else:
                self.unpaired_samples.append(tumor_sample)

    def _get_normal(self, bait_set):
        normal = None
        for normal_sample_id in self.normal_samples:
            normal_sample = self.normal_samples[normal_sample_id]
            normal_baits = normal_sample.bait_set
            if normal_baits.lower() == bait_set.lower():
                if not normal:
                    normal = normal_sample
                else:
                    normal = self._return_more_recent_normal(normal_sample, normal)
        return normal

    def _return_more_recent_normal(self, n1, n2):
        n1_run_date = self._most_recent_date(n1.metadata['runDate'])
        n2_run_date = self._most_recent_date(n2.metadata['runDate'])
        recent_normal = n1
        if n2_run_date > n1_run_date:
            recent_normal = n2
        return recent_normal

    def _most_recent_date(self, dates):
        date = None
        for d in dates:
            current_date = None
            try:
                current_date = dt.strptime(d, '%y-%m-%d')
            except ValueError:
                current_date = dt.strptime(d, '%Y-%m-%d')
            if current_date:
                if not date:
                    date = current_date
                else:
                    if current_date > date:
                        date = current_date
        return date

