import argparse
import sys, os
from datetime import datetime as dt
from pprint import pprint
from .retrieve_samples_by_query import get_samples_from_patient_id


def remove_with_caveats(samples):
    data = list()
    for sample in samples:
        add = True
        igo_id = sample['igo_id']
        sample_name = sample['SM']
        patient_id = sample['patient_id']
        if sample_name is None:
            add = False
            print("Sample name is None for %s; removing from set" % igo_id)
        if patient_id[:2].lower() not in 'c-':
            add = False
            print("Patient ID does not start with expected 'C-' prefix for %s; removing from set" % igo_id)
        if add:
            data.append(sample)
    return data


def get_by_tumor_type(data, tumor_type):
    samples = list()
    for sample in data:
        if tumor_type.lower() in sample['tumor_type'].lower():
            samples.append(sample)
    return samples


def compare_dates(normal, viable_normal, date_string):
    for run_date in normal['run_date']:
        normal_date = dt.strptime(run_date, date_string)
        for vrun_date in viable_normal['run_date']:
            vnormal_date = dt.strptime(vrun_date, date_string)
            if vnormal_date < normal_date:
                viable_normal = normal
    return viable_normal


# From a set of normals, return the ones that have matching patient_id, bait_set, and the most recent
def get_viable_normal(normals, patient_id, bait_set):
    viable_normal = dict()
    for normal in normals:
        if normal['patient_id'] == patient_id and normal['bait_set'] == bait_set:
            if viable_normal:
                try:
                    viable_normal = compare_dates(normal, viable_normal, '%y-%m-%d')
                except ValueError:
                    print("Trying different date parser")
                    viable_normal = compare_dates(normal, viable_normal, '%Y-%m-%d')
            else:
                viable_normal = normal
    return viable_normal


def compile_pairs(samples):
    tumors = get_by_tumor_type(samples, "Tumor")
    normals = get_by_tumor_type(samples, "Normal")

    if len(tumors) == 0:
        print("No tumor samples found; pairing cannot be performed.")
        pprint(samples) 

    # pairing
    pairs = dict()
    pairs['tumor'] = list()
    pairs['normal'] = list()

    for tumor in tumors:
        patient_id = tumor['patient_id']
        if patient_id:
            bait_set = tumor['bait_set']
            normal = get_viable_normal(normals, patient_id, bait_set)
            if normal:
                pairs['tumor'].append(tumor)
                pairs['normal'].append(normal)
            else:
                print("missing normal for sample %s; querying patient %s" % (tumor['igo_id'], patient_id))
                patient_samples = get_samples_from_patient_id(patient_id)
                new_normals = get_by_tumor_type(patient_samples, "Normal")
                new_normal = get_viable_normal(new_normals, patient_id, bait_set)
                if new_normal:
                    pairs['tumor'].append(tumor)
                    pairs['normal'].append(new_normal)
                else:
                    print("No normal found for %s, patient %s" % (tumor['igo_id'], patient_id))
        else:
            print("NoPatientIdError: No patient_id found for %s; skipping." % tumor['igo_id'])
    return pairs


# Outputs pairing data in the form of TUMOR\tNORMAL
# Used in legacy Tempo and Roslin
def create_pairing_info(pairs):
    output_string = ""
    for i in range(0,len(pairs['tumor'])):
        tumor_name = pairs['tumor'][i]['SM']
        normal_name = pairs['normal'][i]['SM']
        output_string += "\t".join([normal_name,tumor_name]) +"\n"
    return output_string