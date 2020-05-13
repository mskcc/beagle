"""
Main module that builds the JSON that needs to be submitted
to the pipeline executor
"""
import logging
import os
import sys
import json
from runner.models import Port
WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)


def load_references():
    """
    Loads reference data from the resources JSON
    """
    data = json.load(open(os.path.join(WORKDIR, 'reference_jsons/helix_filters_resources.json'), 'rb'))
    return data


def get_baits_and_targets(assay, helix_filters_resources):
    """
    From value in assay, retrieve target files from helix_filters_resources
    """
    targets = helix_filters_resources['targets']

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
        return {"class": "File", 'location': str(targets[target_assay]['targets_list'])}
    else:
        error_msg = "ERROR: Targets for Assay not found in helix_filters_resources.json: %s" % assay
        LOGGER.error(error_msg)


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



def list_keys_for_filters():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have a list of values in the JSON
    """
    keys = ['maf_files', 'hisens_cncfs', 'targets_list']
    return set(keys)


def single_keys_for_filters():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have a single of values in the JSON
    """
    keys = ['assay', 'project_prefix', 'is_impact', 'analyst_file', 'portal_file', 'portal_CNA_file', 'analysis_gene_cna_file']
    return set(keys)


def construct_helix_filters_input(run_id_list):
    """
    Main function. From a list of run IDs, build a JSON that combines
    the runs data into one JSON expected by the helix filters pipeline
    """
    input_json = {}
    list_keys = list_keys_for_filters()
    single_keys = single_keys_for_filters()

    for key in list_keys:
        input_json[key] = list()

    for single_run_id in run_id_list:
        port_list = Port.objects.filter(run=single_run_id)
        for single_port in port_list:
            name = single_port.name
            value = single_port.value
            if name == "maf":
                input_json["maf_files"].append(get_file_obj(value))
            if name == "facets_txt_hisens":
                input_json["hisens_cncfs"].append(get_file_obj(value))
            if name == "project_prefix":
                input_json[name] = single_port.value
            if name == "assay":
                if "impact" in single_port.value.lower():
                    input_json["is_impact"] = "True"
                else:
                    input_json["is_impact"] = "False"
                input_json['assay'] = single_port.value

    references = convert_references(input_json['assay'])
    input_json.update(references)
    return input_json


def convert_references(assay):
    """
    Return a dictionary of references based on "assay" for targets_list
    """
    helix_filters_resources = load_references()
    references = dict()
    targets_list = get_baits_and_targets(assay, helix_filters_resources)
    references['targets_list'] = targets_list
    return references


if __name__ == '__main__':
    RUN_ID_LIST = []
    for single_arg in sys.argv[1:]:
        RUN_ID_LIST.append(single_arg)
    INPUT_JSON = construct_helix_filters_input(RUN_ID_LIST)
