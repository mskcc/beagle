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

    Sample class contains paired fastqs
    """
    def __init__(self, sample_id, file_list):
        self.fastqs = Fastqs(file_list)
        self.sample_id = sample_id


    def __str__(self):
        s = self.sample_id
        return s


    def __repr__(self):
        return "{Sample %s}" % self.sample_id


class Fastqs:
    """
    Fastqs class to hold pairs of fastqs

    Does the pairing from a list of files

    The paired bool is True if all of the R1s in file list find a matching R2
    """
    def __init__(self, file_list):
        self.fastqs = dict()
        self.r1 = list()
        self.r2 = list()
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
        for f in r1s:
            self.r1.append(f)
            fastq1 = f.path
            expected_r2 = 'R2'.join(fastq1.rsplit('R1', 1))
            fastq2 = self.get_fastq_from_list(expected_r2, r2s)
            if fastq2:
                self.r2.append(fastq2)
            else:
                print("No fastq R2 found for %s" % f.path)
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
