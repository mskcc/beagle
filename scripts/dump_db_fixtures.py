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

$ dump_db_fixtures.py port_files fd41534c-71eb-4b1b-b3af-e3b1ec3aecde

$ dump_db_fixtures.py run --onefile ca18b090-03ad-4bef-acd3-52600f8e62eb

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
from django.db.models import Prefetch, Max
from django.core import serializers
from pprint import pprint

# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from file_system.models import File, FileMetadata, FileGroup, FileType
from runner.models import Run, RunStatus, Port, PortType, Pipeline, OperatorRun
sys.path.pop(0)

def get_file_filemetadata_from_port(port_instance):
    """
    Get the queryset of all File and FileMetadata entries for a given Port entry
    returns a tuple of type (files_queryset, filemetadata_queryset)
    """
    files_queryset = port_instance.files.all()
    # filemetadata_queryset = FileMetadata.objects.filter(file__in = [i for i in files_queryset])
    filemetata_instances = []
    for file in files_queryset:
        filemetata_instances.append(FileMetadata.objects.filter(file = file).order_by('-version').first())
    return(files_queryset, filemetata_instances)

def dump_request(**kwargs):
    """
    Dump re-loadable fixtures for File and FileMetadata items from a given request
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
    Dump re-loadable Django database fixtures for a Run entry and its associated input and output Port entries
    """
    runID = kwargs.pop('runID')
    onefile = kwargs.pop('onefile')
    output_run_file = "{}.run.json".format(runID)
    output_port_input_file = "{}.run.port.input.json".format(runID)
    output_port_output_file = "{}.run.port.output.json".format(runID)
    output_port_file_input_file = "{}.run.port_file.input.json".format(runID)
    output_port_filemetadata_input_file = "{}.run.port_filemetadata.input.json".format(runID)
    output_port_file_output_file = "{}.run.port_file.output.json".format(runID)
    output_port_filemetadata_output_file = "{}.run.port_filemetadata.output.json".format(runID)
    output_operator_run_file = "{}.run.operator_run.json".format(runID)

    all_data = []
    input_files = []
    input_filemetadatas = []
    output_files = []
    output_filemetadatas = []

    # get the parent Run instance
    run_instance = Run.objects.get(id = runID)

    operator_run_instance = run_instance.operator_run

    # get the Run input and output Port instances
    input_port_queryset = run_instance.port_set.filter(port_type=PortType.INPUT)
    output_port_queryset = run_instance.port_set.filter(port_type=PortType.OUTPUT)

    for item in input_port_queryset:
        files_queryset, filemetata_instances = get_file_filemetadata_from_port(item)
        for file in files_queryset:
            input_files.append(file)
        for filemetadata in filemetata_instances:
            input_filemetadatas.append(filemetadata)

    for item in output_port_queryset:
        files_queryset, filemetata_instances = get_file_filemetadata_from_port(item)
        for file in files_queryset:
            output_files.append(file)
        for filemetadata in filemetata_instances:
            output_filemetadatas.append(filemetadata)

    # save each set of items to individual files by default
    if onefile == False:
        print(json.dumps(json.loads(serializers.serialize('json', [run_instance])), indent=4), file = open(output_run_file, "w"))
        print(json.dumps(json.loads(serializers.serialize('json', [operator_run_instance])), indent=4), file = open(output_operator_run_file, "w"))
        print(json.dumps(json.loads(serializers.serialize('json', input_port_queryset.all())), indent=4), file = open(output_port_input_file, "w"))
        print(json.dumps(json.loads(serializers.serialize('json', output_port_queryset.all())), indent=4), file = open(output_port_output_file, "w"))

        print(json.dumps(json.loads(serializers.serialize('json', input_files)), indent=4), file = open(output_port_file_input_file, "w"))
        print(json.dumps(json.loads(serializers.serialize('json', input_filemetadatas)), indent=4), file = open(output_port_filemetadata_input_file, "w"))

        print(json.dumps(json.loads(serializers.serialize('json', output_files)), indent=4), file = open(output_port_file_output_file, "w"))
        print(json.dumps(json.loads(serializers.serialize('json', output_filemetadatas)), indent=4), file = open(output_port_filemetadata_output_file, "w"))

    # save all items to a single file
    if onefile == True:
        all_data.append(run_instance)
        all_data.append(operator_run_instance)
        for item in input_port_queryset:
            all_data.append(item)
        for item in output_port_queryset:
            all_data.append(item)
        for item in input_files:
            all_data.append(item)
        for item in input_filemetadatas:
            all_data.append(item)
        for item in output_files:
            all_data.append(item)
        for item in output_filemetadatas:
            all_data.append(item)
        print(json.dumps(json.loads(serializers.serialize('json', all_data)), indent=4), file = open(output_run_file, "w"))


def dump_port_files(**kwargs):
    """
    """
    portID = kwargs.pop('portID')
    output_port_file = "{}.port.json".format(portID)
    output_port_file_file = "{}.port.file.json".format(portID)
    output_port_filemetadat_file = "{}.port.filemetadat.json".format(portID)

    port_instance = Port.objects.get(id = portID)
    print(json.dumps(json.loads(serializers.serialize('json', [port_instance])), indent=4), file = open(output_port_file, "w"))

    files_queryset = port_instance.files.all()
    print(json.dumps(json.loads(serializers.serialize('json', files_queryset.all())), indent=4), file = open(output_port_file_file, "w"))

    filemetadata_queryset = FileMetadata.objects.filter(file__in = [i for i in files_queryset])
    print(json.dumps(json.loads(serializers.serialize('json', filemetadata_queryset.all())), indent=4), file = open(output_port_filemetadat_file, "w"))

def dump_pipeline(**kwargs):
    """
    Dump re-loadable Django database fixtures for Pipeline entries and related table fixtures
    """
    pipelineName = kwargs.pop('pipelineName')
    if pipelineName == "all":
        output_pipeline_file = "all_pipeline.json".format(pipelineName)
        output_pipeline_filegroup_file = "all_pipeline.output_file_group.json".format(pipelineName)

        pipelines = Pipeline.objects.all()
        print(json.dumps(json.loads(serializers.serialize('json', pipelines)), indent=4), file = open(output_pipeline_file, "w"))

        file_groups = FileGroup.objects.all()
        print(json.dumps(json.loads(serializers.serialize('json', file_groups)), indent=4), file = open(output_pipeline_filegroup_file, "w"))
    else:
        output_pipeline_file = "{}.pipeline.json".format(pipelineName)
        output_pipeline_filegroup_file = "{}.pipeline.output_file_group.json".format(pipelineName)

        pipeline_instance = Pipeline.objects.get(name = pipelineName)
        print(json.dumps(json.loads(serializers.serialize('json', [pipeline_instance])), indent=4), file = open(output_pipeline_file, "w"))

        print(json.dumps(json.loads(serializers.serialize('json', [pipeline_instance.output_file_group])), indent=4), file = open(output_pipeline_filegroup_file, "w"))

def get_files(value, type):
    """
    Get a file from the database by its Beagle ID or filename
    """
    instances = []
    if type == "bid":
        instances.append(File.objects.get(id = value))
    if type == "filename":
        for item in File.objects.filter(file_name = value):
            instances.append(item)
    for instance in instances:
        yield(instance)

def dump_file(**kwargs):
    """
    Dump re-loadable Django database fixtures for File and FileMetadata items
    """
    bids = kwargs.pop('bids')
    onefile = kwargs.pop('onefile')
    filenames = kwargs.pop('filenames')
    filepaths = kwargs.pop('filepaths')
    get_key = "bid"
    if filenames == True:
        get_key = "filename"
    if filepaths == True:
        get_key = "path"

    all_data = []
    for bid in bids:
        output_label = bid
        if '/' in output_label:
            output_label = output_label.replace('/', '.')

        output_file_file = "{}.file.json".format(output_label)
        output_filemetadata_file = "{}.filemetadata.json".format(output_label)

        # get File entries that match the request ID
        for file_instance in get_files(value = bid, type = get_key):
            file_data = json.loads(serializers.serialize('json', [ file_instance ] ))
            if onefile == False:
                print(json.dumps(file_data, indent=4), file = open(output_filemetadata_file, "w"))

            # get the FileMetadata entries that corresponds to the File
            filemetadata_instance = FileMetadata.objects.get(file = file_instance)
            filemetadata_data = json.loads(serializers.serialize('json', [ filemetadata_instance ]))
            if onefile == False:
                print(json.dumps(filemetadata_data, indent=4), file = open(output_file_file, "w"))

            if onefile == True:
                for item in file_data:
                    all_data.append(item)
                for item in filemetadata_data:
                    all_data.append(item)
    if onefile == True:
        output_file = "all.file_filemetadata.json"
        print(json.dumps(all_data, indent=4), file = open(output_file, "w"))

def dump_file_group(**kwargs):
    """
    Dump the FileGroup fixtures
    """
    fileGroupId = kwargs.pop('fileGroupID')
    output_file_group_file = "{}.file_group.json".format(fileGroupId)
    filegroup_instance = FileGroup.objects.get(id = fileGroupId)
    print(json.dumps(json.loads(serializers.serialize('json', [filegroup_instance])), indent=4), file = open(output_file_group_file, "w"))

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
    run.add_argument('--onefile', action = "store_true", help = 'Put all the outputs into a single file ')
    run.set_defaults(func = dump_run)

    pipeline = subparsers.add_parser('pipeline', help = 'Dump pipeline fixture')
    pipeline.add_argument('pipelineName', help = 'Name of the pipeline to dump')
    pipeline.set_defaults(func = dump_pipeline)

    file = subparsers.add_parser('file', help = 'Dump file fixture')
    file.add_argument('bids', nargs = "*", help = "Beagle db id's of the file to dump")
    file.add_argument('--onefile', action = "store_true", help = 'Put all the outputs into a single file ')
    file.add_argument('--filenames', action = "store_true", help = 'Items passed are file basenames instead of Beagle db IDs ')
    file.add_argument('--filepaths', action = "store_true", help = 'Items passed are file paths instead of Beagle db IDs ')
    file.set_defaults(func = dump_file)

    port_files = subparsers.add_parser('port_files', help = 'Dump port.files fixture')
    port_files.add_argument('portID', help = 'Port ID to dump files for')
    port_files.set_defaults(func = dump_port_files)

    file_group = subparsers.add_parser('filegroup', help = 'Dump filegroup fixture')
    file_group.add_argument('fileGroupID', help = 'FileGroup ID ID to dump items for')
    file_group.set_defaults(func = dump_file_group)

    args = parser.parse_args()
    args.func(**vars(args))

if __name__ == '__main__':
    parse()
