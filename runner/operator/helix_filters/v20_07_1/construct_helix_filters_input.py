"""
Main module that builds the JSON that needs to be submitted
to the pipeline executor
"""
import logging
import os
import sys
import json
from runner.models import Port,Run
from runner.run.processors.file_processor import FileProcessor
from file_system.repository.file_repository import FileRepository
from notifier.helper import generate_sample_data_content
from .bin.oncotree_data_handler.OncotreeDataHandler import OncotreeDataHandler
from django.db.models import Q

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

    if assay.find("IMPACT505") > -1:
        target_assay = "IMPACT505_b37"
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
    file_list = []
    if isinstance(port_obj, list):
        for single_file in port_obj:
            if isinstance(single_file, list):
                file_list.append(get_files_from_port(single_file))
            else:
                file_list.append(get_file_obj(single_file))
    elif isinstance(port_obj, dict):
        file_list.append(get_file_obj(port_obj))
    return file_list


def list_keys_for_filters():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have a list of values in the JSON
    """
    keys = ['mutation_maf_files', 'mutation_svs_maf_files', 'mutation_svs_txt_files',
            'facets_hisens_seg_files', 'facets_hisens_cncf_files', 'targets_list']
    return set(keys)


def single_keys_for_filters():
    """
    Returns a list of keys expected in the JSON to be submitted to the pipeline; these
    keys will have a single of values in the JSON
    """
    keys = ['assay', 'project_prefix', 'is_impact', 'analyst_file', 'portal_file', 'portal_CNA_file', 'analysis_gene_cna_file']
    return set(keys)


def construct_helix_filters_input(argos_run_id_list):
    """
    Main function. From a list of run IDs, build a JSON that combines
    the runs data into one JSON expected by the helix filters pipeline
    """
    input_json = {}
    list_keys = list_keys_for_filters()
    single_keys = single_keys_for_filters()

    for key in list_keys:
        input_json[key] = list()

    for single_run_id in argos_run_id_list:
        port_list = Port.objects.filter(run=single_run_id)
        for single_port in port_list:
            name = single_port.name
            value = single_port.value
            if name == "maf":
                input_json["mutation_maf_files"].append(get_file_obj(value))
            if name == "maf_file":
                input_json["mutation_svs_maf_files"].append(get_file_obj(value))
            if name == "portal_file":
                input_json["mutation_svs_txt_files"].append(get_file_obj(value))
            if name == "facets_txt_hisens":
                input_json["facets_hisens_cncf_files"] = input_json["facets_hisens_cncf_files"] + get_files_from_port(value)
            if name == "facets_seg":
                input_json["facets_hisens_seg_files"] =  input_json["facets_hisens_seg_files"] + get_files_from_port(value)
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

    # some default values
    project_prefix = input_json['project_prefix']
    input_json['project_id'] = project_prefix
    input_json['project_short_name'] = project_prefix
    input_json['project_name'] = project_prefix
    input_json['project_description'] = project_prefix
    input_json['cancer_study_identifier'] = project_prefix

    # Gotta retrieve extra info that's not in the run porto have to query the database
    #
    # Get oncotree codes from samples in project_prefix/request_id FileMetadata
    # will need to change project_prefix to request_id values everywhere, but for now we assume 
    # there is only one project_prefix/request_id per helix_filters run
    input_json['cancer_type'] = get_oncotree_codes(project_prefix)
    input_json['argos_version_string'] = get_argos_pipeline_version(argos_run_id_list)
    input_json['project_pi'] = get_project_pi(argos_run_id_list)
    input_json['request_pi'] = get_request_pi(argos_run_id_list)

    # generate data_clinical file
    input_json['data_clinical_file'] = create_data_clinical_file(argos_run_id_list)

    return input_json


def create_data_clinical_file(run_id_list):
    files = list()
    pipeline_names = set()
    pipeline_githubs = set()
    pipeline_versions = set()
    for run_id in run_id_list:
        argos_run = Run.objects.get(id=run_id)
        pipeline = argos_run.app
        pipeline_names.add(pipeline.name)
        pipeline_githubs.add(pipeline.github)
        pipeline_versions.add(pipeline.version)
        files = files + get_files_from_run(argos_run)
    data_clinical_content = generate_sample_data_content(files,
            pipeline_name=','.join(pipeline_names),
            pipeline_github=','.join(pipeline_githubs),
            pipeline_version=','.join(pipeline_versions))
    data_clinical_content = data_clinical_content.strip()
    return {
                "class": "File",
                "basename": "sample_data_clinical.txt",
                "contents": data_clinical_content
            }


def get_files_from_run(r):
    files = list()
    inp_port = Port.objects.filter(run_id=r.id, name='pair').first()
    for p in inp_port.db_value[0]['R1']:
        files.append(FileProcessor.get_file_path(p['location']))
    for p in inp_port.db_value[0]['R2']:
        files.append(FileProcessor.get_file_path(p['location']))
    for p in inp_port.db_value[0]['zR1']:
        files.append(FileProcessor.get_file_path(p['location']))
    for p in inp_port.db_value[0]['zR2']:
        files.append(FileProcessor.get_file_path(p['location']))
    return files


def build_request_ids_query(data):
    """
    Build complex Q object run id query from given data

    Only does OR queries, as seen in line

       query |= item

    """
    data_query_set = [Q(metadata__requestId=value) for value in set(data)]
    query = data_query_set.pop()
    for item in data_query_set:
        query |= item
    return query


def get_project_pi(run_id_list):
    project_pis = set()
    for run_id in run_id_list:
        argos_run = Run.objects.get(id=run_id)
        project_pi = format_msk_id(argos_run.tags['labHeadEmail'])
        project_pis.add(project_pi)
    return ','.join(list(sorted(project_pis)))


def get_request_pi(run_id_list):
    request_pis = set()
    files = FileRepository.all()
    all_request_ids = set()
    # reducing number of queries
    for run_id in run_id_list:
        argos_run = Run.objects.get(id=run_id)
        run_request_id = argos_run.tags['requestId']
        all_request_ids.add(run_request_id)
    for request_id in all_request_ids:
        investigator_emails = FileRepository.filter(queryset=files,metadata={"requestId": request_id}).values_list('metadata__investigatorEmail', flat=True)
        request_pis = request_pis.union(set(investigator_emails))
    request_pis_final = list()
    for request_pi in request_pis:
        if request_pi:
            request_pis_final.append(format_msk_id(request_pi))
    return ','.join(request_pis_final)


def get_argos_pipeline_version(run_id_list):
    versions = set()
    for run_id in run_id_list:
        argos_run = Run.objects.get(id=run_id)
        versions.add(argos_run.app.version)
    return "_".join(list(sorted(versions)))


def format_msk_id(email_address):
    return email_address.split("@")[0]


def convert_references(assay):
    """
    Return a dictionary of references based on "assay" for targets_list
    """
    helix_filters_resources = load_references()
    references = dict()
    targets_list = get_baits_and_targets(assay, helix_filters_resources)
    references['targets_list'] = targets_list
    references['known_fusions_file'] = {'class': 'File', 'location': str(helix_filters_resources['known_fusions_file']) }
    return references


def get_oncotree_codes(request_id):
    oncotree_dh = OncotreeDataHandler()
    files = FileRepository.all()
    oncotree_codes_tmp = set(FileRepository.filter(queryset=files, metadata={"requestId": request_id}).values_list('metadata__oncoTreeCode', flat=True))
    oncotree_codes = list()
    for val in oncotree_codes_tmp:
        if val:
            oncotree_codes.append(val)
    if not oncotree_codes: # hack; if there are no oncotree codes, just say it's mixed
        return 'mixed'
    shared_nodes = oncotree_dh.find_shared_nodes_by_code_list(oncotree_codes)
    common_anc = oncotree_dh.get_highest_level_shared_node(shared_nodes)
    if common_anc.code.lower() == "tissue":
        common_anc.code = 'mixed'
    return common_anc.code.lower()

if __name__ == '__main__':
    RUN_ID_LIST = []
    for single_arg in sys.argv[1:]:
        RUN_ID_LIST.append(single_arg)
    INPUT_JSON = construct_helix_filters_input(RUN_ID_LIST)
