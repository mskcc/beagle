import sys,os
import json
from pprint import pprint


def format_sample_name(sample_name):
    try:
        if "s_" in sample_name[:2]:
            return sample_name
        elif sample_name is not "":
            sample_name = "s_" + sample_name.replace("-","_")
        else: # sample_name is an empty string; fail this run by re-submitting
            print("cmoSampleName is an empty string.")
            format_sample_name(None)
    except TypeError:
        print("TypeError: cmoSampleName is Nonetype; returning None.")
    return sample_name


def check_samples(samples):
    for rg_id in samples:
        r1 = samples[rg_id]['R1']
        r2 = samples[rg_id]['R2']

        expected_r2 = 'R2'.join(r1.rsplit('R1', 1))
        if expected_r2 != r2:
            print("Mismatched fastqs! Check data:")
            print("R1: %s" % r1)
            print("Expected R2: %s" % expected_r2)
            print("Actual R2: %s" % r2)


def check_and_return_single_values(data):
    single_values = [ 'CN', 'PL', 'SM', 'bait_set', 'patient_id', 'species', 'tumor_type', 'igo_id', 'specimen_type' ]

    for key in single_values:
        value = set(data[key])
        if len(value) == 1:
            data[key] = value.pop()
        else:
            pprint(data)
            print("Expected only one value for %s!" %key)
            print("Check import, something went wrong.")

    # hack; formats LB field so that it is a string
    lb = data['LB']
    if lb is not None:
        data['LB'] = '_and_'.join(lb)
    return data


# TODO: if data is not from the LIMS, these hardcoded values will need to be generalized
# TODO: Add PDX/Xenografts logic (not in LIMS endpoints as of 11/18/2019; should be in 'Specimen Type')
def build_sample(data):
    # note that ID and SM are different field values in ROSLIN (RG_ID and ID, respectively, in ROSLIN)
    # but standardizing it here with what GATK sets bam headers to

    CN = "MSKCC"
    PL = "Illumina"
    samples = dict()

    for i,v in enumerate(data):
        meta = v['metadata']
        libraries = meta['libraries']
        runs = libraries['runs']
        bid = v['id']
        request_id = meta['requestId']
        fpath = v['path']
        fname = v['file_name']
        igo_id = meta['igoId']
        lb = libraries['libraryIgoId']
        bait_set = meta['baitSet']
        tumor_type = meta['tumorOrNormal']
        specimen_type = meta['specimenType']
        species = meta['species']
        cmo_sample_name = format_sample_name(meta['cmoSampleName'])
        flowcell_id = runs['flowCellId']
        barcode_index = libraries['barcodeIndex']
        cmo_patient_id = meta['cmoPatientId']
        pu = flowcell_id
        run_date = runs['runDate']
        if barcode_index:
            pu = '_'.join([flowcell_id,  barcode_index])
        rg_id = pu + "_1"
        if cmo_sample_name:
            rg_id = '_'.join([cmo_sample_name, pu])
        else:
            print("cmoSampleName is None for %s; using PU as read group ID instead." % lb)
        if rg_id not in samples:
            samples[rg_id] = dict()
            sample = dict()
            sample['CN'] = (CN)
            sample['PL'] = (PL)
            sample['PU'] = (pu)
            sample['LB'] = (lb)
            sample['tumor_type'] = (tumor_type)
            sample['ID'] = (rg_id)
            sample['SM'] = (cmo_sample_name)
            sample['species'] = (species)
            sample['patient_id'] = cmo_patient_id
            sample['bait_set'] = bait_set
            sample['igo_id'] = igo_id
            sample['run_date'] = run_date
            sample['specimen_type'] = specimen_type
            sample['request_id'] = request_id
        else:
            sample = samples[rg_id]

        # fastq pairing assumes flowcell id + barcode index are unique per run
        if 'R1' in fname:
            sample['R1'] = fpath
            sample['R1_bid'] = bid
        else:
            sample['R2'] = fpath
            sample['R2_bid'] = bid
        samples[rg_id] = sample
    check_samples(samples)

    result = dict()
    result['CN'] = list()
    result['PL'] = list()
    result['PU'] = list()
    result['LB'] = list()
    result['tumor_type'] = list()
    result['ID'] = list()
    result['SM'] = list()
    result['species'] = list()
    result['patient_id'] = list()
    result['bait_set'] = list() 
    result['igo_id'] = list() 
    result['run_date'] = list()
    result['specimen_type'] = list()
    result['R1'] = list()
    result['R2'] = list()
    result['R1_bid'] = list()
    result['R2_bid'] = list()
    result['request_id'] = list()

    for rg_id in samples:
        sample = samples[rg_id]
        for key in sample:
            result[key].append(sample[key])
    result = check_and_return_single_values(result)

    return result
