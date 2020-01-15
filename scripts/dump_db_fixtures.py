#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to dump database entries for File and FileMetadata for a specific request
into a JSON format that can be re-loaded into the database later with the
`manage.py loaddata file.json` command
This makes it easier to generate database fixtures from pre-existing entires

Usage
-----

$ dump_db_fixtures.py request <requestId>

example:

$ dump_db_fixtures.py request 07951_AP

Output
------

JSON files containing the database entry as a fixture

Example:

- <requestId>.file.json

- <requestId>.filemetadata.json

"""
import os
import sys
import json
import argparse
import django
from django.db.models import Prefetch
from django.core import serializers

# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from file_system.models import File, FileMetadata, FileGroup, FileType
from runner.models import Run, RunStatus, Port, PortType, Pipeline
# from runner.operator.roslin_operator.bin.output_to_qc_input import get_Files_from_Port_queryset
# runner/operator/roslin_operator/bin/output_to_qc_input.py
sys.path.pop(0)


def dump_request(**kwargs):
    """
    """
    requestID = kwargs.pop('requestID')
    output_file_file = "{}.file.json".format(requestID)
    output_filemetadata_file = "{}.filemetadata.json".format(requestID)

    # get FileMetadata entries that match the request ID
    file_instances = FileMetadata.objects.filter(metadata__requestId = requestID)
    print(json.dumps(json.loads(serializers.serialize('json', file_instances)), indent=4), file = open(output_filemetadata_file, "w"))

    # get the File entries that corresponds to the request ID
    queryset = File.objects.prefetch_related(
        Prefetch('filemetadata_set', queryset=
        FileMetadata.objects.select_related('file').order_by('-created_date'))).\
        order_by('file_name').all()
    queryset = queryset.filter(filemetadata__metadata__requestId = requestID)
    print(json.dumps(json.loads(serializers.serialize('json', queryset)), indent=4), file = open(output_file_file, "w"))

def dump_run(**kwargs):
    """
    """
    runID = kwargs.pop('runID')
    output_run_file = "{}.run.json".format(runID)
    output_port_input_file = "{}.port.input.json".format(runID)
    output_port_output_file = "{}.port.output.json".format(runID)

    # get the parent Run instance
    run_instance = Run.objects.get(id = runID)
    print(json.dumps(json.loads(serializers.serialize('json', [run_instance])), indent=4), file = open(output_run_file, "w"))

    # get the Run input and output Port instances
    input_queryset = run_instance.port_set.filter(port_type=PortType.INPUT).all()
    print(json.dumps(json.loads(serializers.serialize('json', input_queryset)), indent=4), file = open(output_port_input_file, "w"))

    output_queryset = run_instance.port_set.filter(port_type=PortType.OUTPUT).all()
    print(json.dumps(json.loads(serializers.serialize('json', output_queryset)), indent=4), file = open(output_port_output_file, "w"))

    # get the input and output File instances
    # output_File_queryset = get_Files_from_Port_queryset(
    #     run_instance.port_set.filter(port_type=PortType.OUTPUT))
    # input_File_queryset = get_Files_from_Port_queryset(
    #     run_instance.port_set.filter(port_type=PortType.INPUT))
    # pprint.pprint(output_File_queryset)
    # pprint.pprint(input_File_queryset)

def dump_pipeline(**kwargs):
    """
    """
    pipelineName = kwargs.pop('pipelineName')
    output_pipeline_file = "{}.pipeline.json".format(pipelineName)
    output_pipeline_filegroup_file = "{}.pipeline.output_file_group.json".format(pipelineName)

    pipeline_instance = Pipeline.objects.get(name = pipelineName)
    print(json.dumps(json.loads(serializers.serialize('json', [pipeline_instance])), indent=4), file = open(output_pipeline_file, "w"))

    print(json.dumps(json.loads(serializers.serialize('json', [pipeline_instance.output_file_group])), indent=4), file = open(output_pipeline_filegroup_file, "w"))

def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description = 'Dump items from Beagle database into a fixture-ready format')
    subparsers = parser.add_subparsers(help ='Sub-commands available')

    # subparser for dumping requests
    request = subparsers.add_parser('request', help = 'Dump File and FileMetadata based on a requestId')
    request.add_argument('requestID', help = 'requestID to dump items for')
    request.set_defaults(func = dump_request)

    run = subparsers.add_parser('run', help = 'Dump output data for pipeline run')
    run.add_argument('runID', help = 'Run ID to dump items for')
    run.set_defaults(func = dump_run)

    pipeline = subparsers.add_parser('pipeline', help = 'Dump pipeline fixture')
    pipeline.add_argument('pipelineName', help = 'Name of the pipeline to dump')
    pipeline.set_defaults(func = dump_pipeline)

    args = parser.parse_args()
    args.func(**vars(args))

if __name__ == '__main__':
    parse()
