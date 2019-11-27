import argparse
import sys, os
import json
import requests
from pprint import pprint
from .make_sample import build_sample
from .extractjson import extract_values
from file_system.models import File, FileMetadata
from django.db.models import Prefetch


def get_samples_from_patient_id(patient_id):
    file_objs = File.objects.prefetch_related(
        Prefetch('filemetadata_set', queryset=
        FileMetadata.objects.select_related('file').order_by('-created_date'))). \
        order_by('file_name')
    files = file_objs.filter(filemetadata__metadata__cmoPatientId=patient_id).all()
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
        samples.append(build_sample(igo_id_group[igo_id]))
    return samples
