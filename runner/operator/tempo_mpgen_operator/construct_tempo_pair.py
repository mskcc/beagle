import os,sys
import argparse
import json
from pprint import pprint
from .bin.make_sample import remove_with_caveats
from .bin.pair_request import compile_pairs


# TODO: generalize
def load_references():
    print(os.getcwd())
    d = json.load(open("runner/operator/tempo_operator/reference_jsons/references_tempo.json", 'rb'))

    return d


def format_sample(data):
    sample = dict()
    sample['R1'] = list()
    sample['R2'] = list()
    sample['sequencing_center'] = data['sequencing_center']
    sample['platform'] = data['platform']
    sample['platform_unit'] = data['platform_unit']
    sample['library'] = data['library']
    sample['tumor_type'] = data['tumor_type']
    sample['read_group_id'] = data['read_group_id']
    sample['species'] = data['species']
    sample['bait_set'] = data['bait_set']
    sample['recipe'] = data['recipe']
    sample['specimen_type'] = data['specimen_type']
    sample['sample_id'] = data['sample_id']
    sample['request_id'] = data['request_id']
    sample['sample_name'] = data['sample_name']
    sample['external_sample_id'] = data['external_sample_id']
    sample['investigator_sample_id'] = data['investigator_sample_id']
    sample['investigator_name'] = data['investigator_name']
    sample['investigator_email'] = data['investigator_email']
    sample['pi'] = data['pi']
    sample['pi_email'] = data['pi_email']
    sample['patient_id'] = data['patient_id']
    sample['sample_class'] = data['sample_class']
    sample['preservation'] = data['preservation']
    sample['data_analyst'] = data['data_analyst']
    sample['data_analyst_email'] = data['data_analyst_email']
    for i in data['R1']:
        sample['R1'].append({'class': 'File', 'location': i})
    for i in data['R2']:
        sample['R2'].append({'class': 'File', 'location': i})
    return sample


def construct_tempo_jobs(samples):
    error_data = remove_with_caveats(samples)
    pairs = compile_pairs(samples)
    number_of_tumors = len(pairs['tumor'])
    tempo_jobs = list()
    for i in range(0, number_of_tumors):
        tumor = pairs['tumor'][i]
        normal = pairs['normal'][i]
        job = dict()
        job['normal_sample'] = format_sample(normal)
        job['tumor_sample'] = format_sample(tumor)
        tempo_jobs.append(job)
    return tempo_jobs, error_data


if __name__ == '__main__':
    request_id = sys.argv[1]

    tempo_jobs = construct_tempo_jobs(request_id)
    pprint(tempo_jobs)
