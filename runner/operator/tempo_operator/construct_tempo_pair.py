import os,sys
import argparse
import json
from pprint import pprint
from .bin.pair_request import compile_pairs, get_by_tumor_type, create_pairing_info
from .bin.retrieve_samples_by_query import get_samples_from_request_id


# TODO: generalize
def load_references():
    print(os.getcwd())
    d = json.load(open("runner/operator/tempo_operator/reference_jsons/references_tempo.json", 'rb'))

    return d


# TODO: This is ROSLIN-formatted, note the confusing IDs
def format_sample(data):
    sample = dict()
    sample['ID'] = data['SM'] # TODO: change someday
    sample['CN'] = data['CN']
    sample['LB'] = data['LB']
    sample['PL'] = data['PL']
    sample['PU'] = data['PU']
    sample['R1'] = list()
    sample['R2'] = list()
    for i in data['R1']:
        sample['R1'].append({'class': 'File', 'location': 'juno://' + i})
    for i in data['R2']:
        sample['R2'].append({'class': 'File', 'location': 'juno://' + i})
    sample['RG_ID'] = data['ID']
    sample['adapter'] = 'AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATGAGCATCTCGTATGCCGTCTTCTGCTTG' # Don't think tempo needs these, but putting them in for now
    sample['adapter2'] = 'AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT'
    sample['bwa_output'] = sample['ID'] + '.bam'

    return sample


def construct_tempo_jobs(samples):
    pairs = compile_pairs(samples)
    number_of_tumors = len(pairs['tumor'])
    tempo_jobs = list()
    for i in range(0, number_of_tumors):
        references = load_references()
        tumor = pairs['tumor'][i]
        normal = pairs['normal'][i]
        job = dict()
        job['normal_sample'] = format_sample(normal)
        job['tumor_sample'] = format_sample(tumor)
        job.update(references)
        tempo_jobs.append(job)
    return tempo_jobs


if __name__ == '__main__':
    request_id = sys.argv[1]

    tempo_jobs = construct_tempo_jobs(request_id)
    pprint(tempo_jobs)
