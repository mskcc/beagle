from django.conf import settings
from django.db.models import Q

from file_system.repository.file_repository import FileRepository

from .files_object import FilesObj
from .pair_object import PairObj
from .sample_dmp import SampleDMP
from .sample_file_object import SampleFile
from .sample_igo import SampleIGO
from .sample_pooled_normal import SamplePooledNormal


class PatientObj:
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.samples_igo = list()
        self.samples_dmp = list()
        self.samples_pn = list()
        self.pair = None

    def add_sample_igo(self, sample):
        self.samples_igo.append(sample)

    def add_sample_dmp(self, sample):
        self.samples_dmp.append(sample)

    def add_sample_pn(self, sample):
        self.samples_pn.append(sample)
