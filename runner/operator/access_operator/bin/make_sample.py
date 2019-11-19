import sys,os
import json
from pprint import pprint


def format_sample_name(sample_name):
    try:
        if "s_" in sample_name[:2]:
            return sample_name
        else:
            sample_name = "s_" + sample_name.replace("-","_")
    except TypeError:
        print("cmoSampleName is Nonetype; returning None.")
    return sample_name


def generate_results(results):
    CN = "MSKCC"
    PL = "Illumina"

    samples = dict()

    for i, v in enumerate(results):
        meta = v['metadata']
        libraries = meta['libraries']
        runs = libraries['runs']
        bid = v['id']
        fpath = v['path']
        fname = v['file_name']
        igo_id = meta['igoId']
        lb = libraries['libraryIgoId']
        bait_set = meta['baitSet']
        tumor_type = meta['tumorOrNormal']
        species = meta['species']
        cmo_sample_name = meta['cmoSampleName']
        flowcell_id = runs['flowCellId']
        barcode_index = libraries['barcodeIndex']
        cmo_patient_id = meta['cmoPatientId']
        pu = flowcell_id
        run_date = runs['runDate']
        if barcode_index:
            pu = '_'.join([flowcell_id, barcode_index])

        if not cmo_sample_name:
            cmo_sample_name = cmo_patient_id + "_" + pu
        else:
            print("cmoSampleName is None for %s; using PU as read group ID instead." % lb)
        rg_id = cmo_sample_name

        if rg_id not in samples:
            samples[rg_id] = dict()
            sample = dict()
            sample['request_id'] = meta['requestId']
            sample['read_group_sequnecing_center'] = (CN)
            sample['read_group_sequencing_platform'] = (PL)
            sample['read_group_platform_unit'] = (pu)
            sample['read_group_library'] = (lb)
            sample['tumor_type'] = (tumor_type)
            sample['read_group_identifier'] = (rg_id)
            sample['read_group_sample_name'] = (cmo_sample_name)
            sample['species'] = (species)
            sample['patient_id'] = cmo_patient_id
            sample['bait_set'] = bait_set
            sample['igo_id'] = igo_id
            sample['run_date'] = run_date

            # TODO: Adding fields
            sample["collapsing_aln_output_file_name"] = cmo_sample_name + "_unfiltered.sam"
            sample["collapsing_picard_output_file_name"] = cmo_sample_name + "_unfiltered.bam"
            sample["output_name_collapsed_gzip_R1"] = cmo_sample_name + "_collapsed_R1.fastq.gz"
            sample["output_name_collapsed_gzip_R2"] = cmo_sample_name + "_collapsed_R2.fastq.gz"
            sample["sort_first_pass_output_file_name"] = cmo_sample_name + "_collapsing_first_pass.txt"
            sample["standard_aln_output_file_name"] = cmo_sample_name + "_standard.sam"
            sample["standard_picard_addrg_output_filename"] = cmo_sample_name + "_standard.bam"
        else:
            sample = samples[rg_id]

        if 'R1' in fname:
            sample['fastq1'] = fpath
            sample['fastq1_bid'] = str(bid)
        else:
            sample['fastq2'] = fpath
            sample['fastq2_bid'] = str(bid)
        samples[rg_id] = sample
    check_samples(samples)

    result = dict()
    result['read_group_sequnecing_center'] = list()
    result['read_group_sequencing_platform'] = list()
    result['read_group_platform_unit'] = list()
    result['read_group_library'] = list()
    result['request_id'] = list()
    result['tumor_type'] = list()
    result['read_group_identifier'] = list()
    result['read_group_sample_name'] = list()
    result['species'] = list()
    result['patient_id'] = list()
    result['bait_set'] = list()
    result['igo_id'] = list()
    result['run_date'] = list()
    result['fastq1'] = list()
    result['fastq2'] = list()
    result['fastq1_bid'] = list()
    result['fastq2_bid'] = list()
    result["collapsing_aln_output_file_name"] = list()
    result["collapsing_picard_output_file_name"] = list()
    result["output_name_collapsed_gzip_R1"] = list()
    result["output_name_collapsed_gzip_R2"] = list()
    result["sort_first_pass_output_file_name"] = list()
    result["standard_aln_output_file_name"] = list()
    result["standard_picard_addrg_output_filename"] = list()

    for rg_id in samples:
        sample = samples[rg_id]
        for key in sample:
            result[key].append(sample[key])
    result = check_and_return_single_values(result)

    print(result)
    return result


def check_samples(samples):
    for rg_id in samples:
        r1 = samples[rg_id]['fastq1']
        r2 = samples[rg_id]['fastq2']

        expected_r2 = 'R2'.join(r1.rsplit('R1', 1))
        if expected_r2 != r2:
            print("Mismatched fastqs! Check data:")
            print("R1: %s" % r1)
            print("Expected R2: %s" % expected_r2)
            print("Actual R2: %s" % r2)


def check_and_return_single_values(data):
    single_values = ['read_group_sequnecing_center', 'read_group_library', 'read_group_sequencing_platform',
                     'read_group_sample_name', 'bait_set',
                     'patient_id', 'species', 'tumor_type', 'igo_id']

    for key in single_values:
        value = set(data[key])
        if len(value) == 1:
            data[key] = value.pop()
        else:
            pprint(data)
            print("Expected only one value for %s!" % key)
            print("Check import, something went wrong.")
    return data
