import os,sys
import argparse
import json
import pprint


# TODO: generalize
def load_references():
    d = json.load(open("runner/operator/access_operator/reference_jsons/access_references.json", 'rb'))
    return d


# Access module 1 uses 'fastq1' and 'fastq2' as variable names instead of 'R1' and 'R2';
#   this gave opportunity to convert R1/R2 to JSON file objects
def convert_to_file(sample):
    sample['fastq1'] = list()
    sample['fastq2'] = list()
    for i in sample['R1']:
        sample['fastq1'].append({'class': 'File', 'location': 'juno://' + i})
    for i in sample['R2']:
        sample['fastq2'].append({'class': 'File', 'location': 'juno://' + i})
    return sample


def construct_access_jobs(samples):
    references = load_references()
    access_jobs = list()
    for i in range(0, len(samples)):
        sample = samples[i]
        project_id = sample['request_id']
        assay = sample['bait_set']
        sample = convert_to_file(sample)
        job = dict()
        job.update(sample)
        job.update(references)
        access_jobs.append(job)
    return access_jobs
