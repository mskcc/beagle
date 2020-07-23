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
        for sample_name in data:
            sample = data[sample_name]
            samples[sample_name] = tempo_sample.TempoSample(sample_name, sample)
        return samples

    def _characterize_samples(self):
        for sample_name in self._samples:
            sample = self._samples[sample_name]
            sample_class = sample.sample_class
            if not sample_class:
                self.conflict_samples[sample_name] = sample
            elif isinstance(sample_class, list):
                self.conflict_samples[sample_name] = sample
            elif not sample_name: # sample name empty
                 self.conflict_samples[sample_name] = sample
            elif 'sampleNameMalformed' in sample.metadata['cmoSampleName']: # cmo sample name is no good 
                 self.conflict_samples[sample_name] = sample
            else:
                if "normal" in sample_class.lower():
                    self.normal_samples[sample_name] = sample
                else:
                    self.tumor_samples[sample_name] = sample

    def _pair_samples(self):
        for tumor_sample_name in self.tumor_samples:
            tumor_sample = self.tumor_samples[tumor_sample_name]
            tumor_baits = tumor_sample.bait_set
            normal = self._get_normal(tumor_baits)
            if normal:
                self.sample_pairing.append([tumor_sample, normal])
            else:
                self.unpaired_samples.append(tumor_sample)

    def _get_normal(self, bait_set):
        normal = None
        for normal_sample_name in self.normal_samples:
            normal_sample = self.normal_samples[normal_sample_name]
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

    def get_sample(self, sample_name):
        try:
            return self._samples[sample_name]
        except:
            return None

    def create_mapping_string(self):
        s = ""
        seen = set()
        for pair in self.sample_pairing:
            tumor_sample = pair[0]
            normal_sample = pair[1]
            s +=  self.get_mapping_string(tumor_sample)
            if normal_sample not in seen:
                s +=  self.get_mapping_string(normal_sample)
                seen.add(normal_sample)
        return s

    def get_mapping_string(self, sample):
        s = ""
        target = sample.bait_set
        fastqs = sample.fastqs
        cmo_sample_name = sample.cmo_sample_name
        if fastqs.paired:
            num_fq_pairs = len(fastqs.r1)
            for i in range(0, num_fq_pairs):
                r1 = fastqs.r1[i].path
                r2 = fastqs.r2[i].path
                s += "%s\t%s\t%s\t%s\t%i\n" % (cmo_sample_name, target, r1, r2, num_fq_pairs)
        return s

    def create_pairing_string(self):
        pairing = ""
        if self.sample_pairing:
            for pair in self.sample_pairing:
                tumor = pair[0].cmo_sample_name
                normal = pair[1].cmo_sample_name
                pairing += "%s\t%s\n" % (normal, tumor)
        return pairing


    def create_unpaired_string(self, fields):
        s = ""
        for sample in self.unpaired_samples:
            data = [ ";".join(list(set(sample.metadata[field]))).strip() for field in fields ] # hack; probably need better way to map fields to unpaired txt file
            possible_reason = self._get_possible_reason(sample)
            s += "\n" + "\t".join(data) + "\t" + possible_reason
        return s

    def _get_possible_reason(self, sample):
        num_normals = len(self.normal_samples)
        if num_normals == 0:
            return "No normals for patient"
        matching_baits = False
        for sample_name in self.normal_samples:
            normal = self.normal_samples[sample_name]
            if normal.bait_set.lower() == sample.bait_set.lower():
                matching_baits = True
        if not matching_baits:
            return "No normal sample has same bait set as tumor in patient"
        first_half_of_2017 = False
        run_dates = sample.metadata['runDate'].split(";")
        for run_date in run_dates:
            try:
                current_date = dt.strptime(d, '%y-%m-%d')
            except ValueError:
                current_date = dt.strptime(d, '%Y-%m-%d')
            if current_date < dt(2017, 6, 1):
                first_half_of_2017 = True
        if first_half_of_2017:
            return "Sample run date first half of 2017; normal may have been sequenced in 2016?"
        return ""

    def create_conflict_string(self, fields):
        s = ""
        for sample_name in self.conflict_samples:
            sample = self.conflict_samples[sample_name]
            data = [ ";".join(list(set(sample.metadata[field]))).strip() for field in fields ] # hack; probably need better way to map fields to unpaired txt file
            conflicts = []
            if "sampleNameMalformed" in sample.metadata['cmoSampleName']:
                conflicts.append("incorrect CMO Sample Name")
            if not "".join(sample.metadata['sampleClass']):
                    conflicts.append("no sample class")
            multiple_values = [ "" + field + "[" + ";".join(list(set(sample.metadata[field]))).strip() + "]" for field in sample.conflict_fields ]
            conflicts = conflicts + multiple_values
            s += "\n" + "\t".join(data) + "\t" + ";".join(conflicts)
        return s
