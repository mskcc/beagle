"""
Main module that builds the JSON that needs to be submitted
to the pipeline executor
"""

import os
import sys
import json
from runner.models import Port
WORKDIR = os.path.dirname(os.path.abspath(__file__))


def load_references():
    """
    Loads QC reference data from the resources JSON
    """
    data = json.load(open(os.path.join(WORKDIR, 'reference_jsons/roslin_qc_resources.json'), 'rb'))
    return data


def get_baits_and_targets(assay, roslin_qc_resources):
    """
    From value in assay, retrieve target files (mainly fp_genotypes) from roslin_qc_resources
    """
    targets = roslin_qc_resources['targets']

    target_assay = assay

    if assay.find("IMPACT410") > -1:
        target_assay = "IMPACT410_b37"
    if assay.find("IMPACT468") > -1:
        target_assay = "IMPACT468_b37"
    if assay.find("IMPACT341") > -1:
        target_assay = "IMPACT341_b37"
    if assay.find("IDT_Exome_v1_FP") > -1:
        target_assay = "IDT_Exome_v1_FP_b37"
    if assay.find("IMPACT468+08390") > -1:
        target_assay = "IMPACT468_08390"
    if assay.find("IMPACT468+Poirier_RB1_intron_V2") > -1:
        target_assay = "IMPACT468_08050"

    if target_assay in targets:
        return {"class": "File", 'location': str(targets[target_assay]['fp_genotypes'])}
    else:
        error_msg = "ERROR: Targets for Assay not found in roslin_qc_resources.json: %s" % assay
        print >>sys.stderr, error_msg


def create_cwl_file_obj(file_path):
    """
    Given a filepath, return a dictionary with class File and JUNO-specific URI
    """
    cwl_file_obj = {'class': 'File', 'location': "juno://%s" % file_path}
    return cwl_file_obj


def get_file_obj(file_obj):
    """
    Given file_obj, construct a dictionary of class File, that file's
    JUNO-specific URI file path, and a list of secondary files with
    JUNO-specific URI file paths
    """
    secondary_file_list = []
    file_location = file_obj['location'].replace('file://', '')
    if 'secondaryFiles' in file_obj:
        for single_secondary_file in file_obj['secondaryFiles']:
            secondary_file_location = single_secondary_file['location'].replace(
                'file://', '')
            secondary_file_cwl_obj = create_cwl_file_obj(
                secondary_file_location)
            secondary_file_list.append(secondary_file_cwl_obj)
    file_cwl_obj = create_cwl_file_obj(file_location)
    if secondary_file_list:
        file_cwl_obj['secondaryFiles'] = secondary_file_list
    return file_cwl_obj


def get_files_from_port(port_obj):
    """
    From port object, retrieve a list of files
    """
    file_list = []
    if isinstance(port_obj, list):
        for single_file in port_obj:
            file_list.append(get_file_obj(single_file))
    elif isinstance(port_obj, dict):
        file_list.append(get_file_obj(port_obj))
    return file_list


def list_keys_for_qc():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have a list of values in the JSON
    """
    keys = ['tumor_bams', 'normal_bams', 'tumor_sample_names', 'normal_sample_names',
            'hotspot_list_maf', 'conpair_markers', 'md_metrics', 'hs_metrics',
            'insert_metrics', 'per_target_coverage', 'qual_metrics', 'doc_basecounts',
            'conpair_pileups', 'directories', 'files', 'mafs']
    return set(keys)


def single_keys_for_qc():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have one value in the JSON
    """
    keys = ["project_prefix", "genome", "assay", "pi", "pi_email"]
    return keys


def construct_roslin_qc_input(run_id_list):
    """
    Main function. From a list of run IDs, build a JSON that combines
    the runs data into one JSON expected by the Roslin QC pipeline
    """
    input_json = {}
    list_keys = list_keys_for_qc()
    single_keys = single_keys_for_qc()

    for key in list_keys:
        input_json[key] = list()

    for key in single_keys:
        input_json[key] = ""

    for single_run_id in run_id_list:
        port_list = Port.objects.filter(run=single_run_id)
        for single_port in port_list:
            name = single_port.name
            value = single_port.value
            # Assign genome, assay, pi, pi_email, project_prefix, ref_fasta here
            if name in single_keys:
                if not input_json[name]:
                    input_json[name] = value
            if name == "tumor_bam":
                input_json['tumor_bams'].append(get_file_obj(value))
            if name == "normal_bam":
                input_json['normal_bams'].append(get_file_obj(value))
            if name == "tumor_sample_name":
                input_json['tumor_sample_names'].append(value)
            if name == "normal_sample_name":
                input_json['normal_sample_names'].append(value)
            if name == "maf_file":
                input_json["mafs"].append(get_file_obj(value))
            if name == "md_metrics":
                input_json[name].append(get_files_from_port(value))
            if name == "insert_metrics":
                input_json[name].append(get_files_from_port(value))
            if name == "hs_metrics":
                input_json[name].append(get_files_from_port(value))
            if name == "per_target_coverage":
                input_json[name].append(get_files_from_port(value))
            if name == "qual_metrics":
                input_json[name].append(get_files_from_port(value))
            if name == "doc_basecounts":
                input_json[name].append(get_files_from_port(value))
            if name == "conpair_pileups":
                input_json[name].append(get_files_from_port(value))

    references = convert_references(input_json['assay'])
    input_json.update(references)
    return input_json


def convert_references(assay):
    """
    Return a dictionary of references based on "assay" for fp_genotypes; other keys
    are expected to be static but are still in the roslin_qc_resources reference file
    in case it varies in the future
    """
    roslin_qc_resources = load_references()
    references = dict()
    fp_genotypes = get_baits_and_targets(assay, roslin_qc_resources)
    references['fp_genotypes'] = fp_genotypes
    references['ref_fasta'] = {'class': 'File', 'location': roslin_qc_resources['ref_fasta']}
    references['conpair_markers'] = roslin_qc_resources['conpair_markers']
    references['hotspot_list_maf'] = {'class': 'File',
                                      'location': roslin_qc_resources['hotspot_list_maf']}
    return references


if __name__ == '__main__':
    RUN_ID_LIST = []
    for single_arg in sys.argv[1:]:
        RUN_ID_LIST.append(single_arg)
    INPUT_JSON = construct_roslin_qc_input(RUN_ID_LIST)
