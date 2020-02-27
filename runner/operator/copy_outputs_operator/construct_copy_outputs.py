import os,sys
import argparse
import json
from pprint import pprint
from runner.models import Port


def get_roslin_output_description():
  output_description = {'bams' : 'bam',
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
    'facets_png': 'facets',
    'facets_txt_hisens': 'facets',
    'facets_txt_purity': 'facets',
    'facets_out': 'facets',
    'facets_rdata': 'facets',
    'facets_seg': 'facets',
    'facets_counts': 'facets',
    'merged_file_unfiltered': 'vcf',
    'merged_file': 'vcf',
    'maf_file': 'maf',
    'portal_file': 'maf',
    'maf': 'maf'}
  return output_description

def create_cwl_file_obj(file_path):
  cwl_file_obj = {'class': 'File', 'path': file_path}
  return cwl_file_obj


def get_file_obj(file_obj):
  file_list = []
  secondary_file_list = []
  file_location = file_obj['location'].replace('file://','')
  file_cwl_obj = create_cwl_file_obj(file_location)
  file_list.append(file_cwl_obj)
  if 'secondaryFiles' in file_obj:
    for single_secondary_file in file_obj['secondaryFiles']:
      secondary_file_location = single_secondary_file['location'].replace('file://','')
      secondary_file_cwl_obj = create_cwl_file_obj(secondary_file_location)
      secondary_file_list.append(secondary_file_cwl_obj)
  return {'files': file_list, 'secondary_files': secondary_file_list}

def get_files_from_port(port_obj):
  file_list = []
  list_of_pairs = False
  if isinstance(port_obj,list):
    for single_file in port_obj:
      file_list.append(get_file_obj(single_file))
  elif isinstance(port_obj,dict):
    file_list.append(get_file_obj(port_obj))
  return file_list

def list_file_paths(file_obj_list):
  list_of_files = []
  for single_file_obj in file_obj_list:
    list_of_files = list_of_files + single_file_obj['files']
    list_of_files = list_of_files + single_file_obj['secondary_files']
  return list_of_files

def list_file_paths(file_obj_list):
  list_of_files = []
  for single_file_obj in file_obj_list:
    list_of_files = list_of_files + single_file_obj['files']
    list_of_files = list_of_files + single_file_obj['secondary_files']
  return list_of_files


def construct_copy_outputs_input(run_id_list):
  pair_list = []
  input_json = {}
  facets_list = []
  pair_number = 0
  output_description = get_roslin_output_description()

  for single_run_id in run_id_list:
    port_list = Port.objects.filter(run=single_run_id)
    for single_port in port_list:
      if single_port.name == 'pair':
        port_pair = single_port.value
        facets_dict = {'normal_id': port_pair[1]['ID'], 'tumor_id': port_pair[0]['ID'], 'files': []}
        facets_list.append(facets_dict)
    for single_port in port_list:
      port_name = single_port.name
      if port_name in output_description:
        port_type = output_description[port_name]
        if port_type != 'qc':
          port_files = get_files_from_port(single_port.value)
          if port_type != 'facets':
            if port_type not in input_json:
              input_json[port_type] = list_file_paths(port_files)
            else:
              input_json[port_type] = input_json[port_type] + list_file_paths(port_files)
          else:
            for single_facets_file in port_files:
              facets_list[pair_number]['files'] = facets_list[pair_number]['files'] + list_file_paths([single_facets_file])
    input_json['facets'] = facets_list
    pair_number = pair_number + 1
  return input_json


if __name__ == '__main__':
  run_id_list = []
  #run_id_list=['ca18b090-03ad-4bef-acd3-52600f8e62eb','fd97c0f5-ca03-4134-aeee-4fbb07394638']
  for single_arg in sys.argv[1:]:
    run_id_list.append(single_arg)
  input_json = construct_copy_outputs_input(run_id_list)
  pprint(input_json)