import re
from django.db.models import Q
from rest_framework import serializers
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from file_system.repository.file_repository import FileRepository


class Sample:
    """
    Sample class
    It takes a queryset object containing a list of files, file_list,
    which itself contains File Objects.

    From Files metadata, remove duplicates from fields with best knowledge
    available.

    Sample class contains paired fastqss
    """
    def __init__(self, file_list):
        self.metadata = dict()
        metadata_list = [ i.metadata for i in file_list ]
        for metadata in metadata_list:
            for key in metadata:
                if key not in self.metadata:
                    self.metadata[key] = list()
                self.metadata[key].append(metadata[key])
        self.metadata.pop("R")
        self.dedupe_metadata_values()
        self.fastqs = Fastqs(file_list)


    def dedupe_metadata_values(self):
        for key in self.metadata:
            values = self.metadata[key]
            if not self.values_are_list(key):
                # remove empty strings
                values = [i for i in values if i]
                if len(set(values)) == 1:
                    self.metadata[key] = values[0]
                else:
                    value = set(values)
                    self.metadata[key] = ','.join(value)
            else:
                # remove duplicate list values
                values_set = set(tuple(x) for x in values)
                values = [ list(x) for x in values_set ]
                self.metadata[key] = values


    def values_are_list(self, key):
        for ele in self.metadata[key]:
            if not isinstance(ele, list):
                return False
        return True


    def __str__(self):
        keys_for_str = [ 'sampleName', 'requestId', 'sampleId', 'patientId', 'specimenType' ]
        s = ""
        for key in keys_for_str:
            if not isinstance(self.metadata[key], str):
                data = ",".join(self.metadata[key])
            else:
                data = self.metadata[key]
            s += "%s: %s\n" % (key, data)
        return s


    def __repr__(self):
        return "{Sample %s}" % self.metadata['sampleName']


class Fastqs:
    def __init__(self, file_list):
        self.fastqs = dict()
        self.fastqs['R1'] = list()
        self.fastqs['R2'] = list()
        self.paired = True
        self.set_R(file_list)


    def set_R(self, file_list):
        """
        From the file list, retrieve R1 and R2 fastq files

        Uses get_fastq_from_list() to find R2 pair.
        """
        r1s = list()
        r2s = list()
        for i in file_list:
            f = i.file
            r = i.metadata['R']
            if r == "R1":
                r1s.append(f)
            if r == "R2":
                r2s.append(f)
        for r1 in r1s:
            self.fastqs['R1'].append(r1)
            fastq1 = r1.path
            expected_r2 = 'R2'.join(fastq1.rsplit('R1', 1))
            fastq2 = self.get_fastq_from_list(expected_r2, r2s)
            if fastq2:
                self.fastqs['R2'].append(fastq2)
            else:
                print("No fastq R2 found for %s" % r1.path)
                self.paired = False


    def get_fastq_from_list(self, fastq_path, fastq_files):
        """
        Given fastq_path, find it in the list of fastq_files and return
        that File object
        """
        for f in fastq_files:
            fpath = f.path
            if fastq_path == fpath:
                return f
        return None
