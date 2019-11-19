import os,sys
import argparse
import json
import pprint


# TODO: generalize
def load_references():
    d = json.load(open("runner/operator/access_operator/reference_jsons/access_references.json", 'rb'))
    return d


def construct_access_jobs(samples):
    references = load_references()
    access_jobs = list()
    for i in range(0, len(samples)):
        sample = samples[i]
        project_id = sample['request_id']
        assay = sample['bait_set']
        job = dict()
        job.update(sample)
        job.update(references)
        access_jobs.append(job)
    return access_jobs
