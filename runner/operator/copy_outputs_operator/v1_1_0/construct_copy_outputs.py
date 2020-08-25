import os
import sys
import argparse
import json
from pprint import pprint
from runner.models import Port, Run
from runner.run.processors.file_processor import FileProcessor
from notifier.helper import generate_sample_data_content


def get_argos_output_description():
    output_description = {'normal_bam': 'bam',
                          'tumor_bam': 'bam',
                          'clstats1': 'qc',
                          'clstats2': 'qc',
                          'md_metrics': 'qc',
                          'as_metrics': 'qc',
                          'hs_metrics': 'qc',
                          'insert_metrics': 'qc',
                          'insert_pdf': 'qc',
                          'per_target_coverage': 'qc',
                          'qual_metrics': 'qc',
                          'qual_pdf': 'qc',
                          'doc_basecounts': 'qc',
                          'gcbias_pdf': 'qc',
                          'gcbias_metrics': 'qc',
                          'gcbias_summary': 'qc',
                          'conpair_pileups': 'qc',
                          'mutect_vcf': 'vcf',
                          'mutect_callstats': 'vcf',
                          'vardict_vcf': 'vcf',
                          'combine_vcf': 'vcf',
                          'annotate_vcf': 'vcf',
                          'vardict_norm_vcf': 'vcf',
                          'mutect_norm_vcf': 'vcf',
                          'merged_file_unfiltered': 'vcf',
                          'merged_file': 'vcf',
                          'maf_file': 'maf',
                          'portal_file': 'maf',
                          'maf': 'maf'}
    return output_description


def create_cwl_file_obj(file_path):
    cwl_file_obj = {'class': 'File', 'location': "juno://%s" % file_path}
    return cwl_file_obj


def get_file_obj(file_obj):
    file_list = []
    secondary_file_list = []
    file_location = file_obj['location'].replace('file://', '')
    file_cwl_obj = create_cwl_file_obj(file_location)
    file_list.append(file_cwl_obj)
    if 'secondaryFiles' in file_obj:
        for single_secondary_file in file_obj['secondaryFiles']:
            secondary_file_location = single_secondary_file['location'].replace(
                'file://', '')
            secondary_file_cwl_obj = create_cwl_file_obj(
                secondary_file_location)
            secondary_file_list.append(secondary_file_cwl_obj)
    return {'files': file_list, 'secondary_files': secondary_file_list}


def get_files_from_port(port_obj):
    file_list = []
    list_of_pairs = False
    if isinstance(port_obj, list):
        for single_file in port_obj:
            file_list.append(get_file_obj(single_file))
    elif isinstance(port_obj, dict):
        file_list.append(get_file_obj(port_obj))
    return file_list


def list_file_paths(file_obj_list):
    list_of_files = []
    for single_file_obj in file_obj_list:
        list_of_files = list_of_files + single_file_obj['files']
        list_of_files = list_of_files + single_file_obj['secondary_files']
    return list_of_files


def construct_copy_outputs_input(run_id_list):
    input_json = {}
    output_description = get_argos_output_description()
    project_prefix = set()

    for single_run_id in run_id_list:
        port_list = Port.objects.filter(run=single_run_id)
        for single_port in port_list:
            if single_port.name == "project_prefix":
                project_prefix.add(single_port.value)
        for single_port in port_list:
            port_name = single_port.name
            if port_name in output_description:
                port_type = output_description[port_name]
                if port_type != 'qc':
                    port_files = get_files_from_port(single_port.value)
                    if port_type not in input_json:
                        input_json[port_type] = list_file_paths(port_files)
                    else:
                        input_json[port_type] = input_json[port_type] + \
                            list_file_paths(port_files)
    input_json["project_prefix"] = "_".join(project_prefix)
    return input_json


def generate_sample_pairing_and_mapping_files(run_ids):

    sample_pairing = ""
    sample_mapping = ""

    runs = Run.objects.filter(id__in=run_ids)

    request_id_set = set()

    files = list()

    if runs:
        pipeline = runs[0].app

    for r in runs:
        request_id_set.add(r.tags['requestId'])
        inp_port = Port.objects.filter(run_id=r.id, name='pair').first()
        tumor_sample_name = inp_port.db_value[0]['ID']
        for p in inp_port.db_value[0]['R1']:
            sample_mapping += "\t".join(
                [tumor_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[0]['R2']:
            sample_mapping += "\t".join(
                [tumor_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[0]['zR1']:
            sample_mapping += "\t".join(
                [tumor_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[0]['zR2']:
            sample_mapping += "\t".join(
                [tumor_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        normal_sample_name = inp_port.db_value[1]['ID']
        for p in inp_port.db_value[1]['R1']:
            sample_mapping += "\t".join(
                [normal_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[1]['R2']:
            sample_mapping += "\t".join(
                [normal_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[1]['zR1']:
            sample_mapping += "\t".join(
                [normal_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[1]['zR2']:
            sample_mapping += "\t".join(
                [normal_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))
        for p in inp_port.db_value[1]['bam']:
            sample_mapping += "\t".join(
                [normal_sample_name, FileProcessor.get_file_path(p['location'])]) + "\n"
            files.append(FileProcessor.get_file_path(p['location']))

        sample_pairing += "\t".join([normal_sample_name, tumor_sample_name]) + "\n"

    if runs:
        data_clinical = generate_sample_data_content(files,
                                                     pipeline_name=pipeline.name,
                                                     pipeline_github=pipeline.github,
                                                     pipeline_version=pipeline.version)

    return sample_mapping, sample_pairing, data_clinical


if __name__ == '__main__':
    run_id_list = []
    for single_arg in sys.argv[1:]:
        run_id_list.append(single_arg)
    input_json = construct_copy_outputs_input(run_id_list)
    pprint(input_json)
