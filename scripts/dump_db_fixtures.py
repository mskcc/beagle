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

Output
------

JSON files containing the database entry as a fixture

Example:

- <requestId>.file.json

- <requestId>.filemetadata.json

"""
# fmt: off
import os
import sys
import django
# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from runner.models import Run, RunStatus, Port, PortType, Pipeline
from file_system.models import File, FileMetadata, FileGroup, FileType
sys.path.pop(0)
import json
import argparse

from django.db.models import Prefetch
from django.core import serializers
from pprint import pprint
# fmt: on


def dump_request(**kwargs):
    """
    Dump re-loadable fixtures for File and FileMetadata items from a given request
    """
    requestID = kwargs.pop("requestID")
    output_file_file = "{}.file.json".format(requestID)
    output_filemetadata_file = "{}.filemetadata.json".format(requestID)

    # get FileMetadata entries that match the request ID
    file_instances = FileMetadata.objects.filter(metadata__igoRequestId=requestID)
    print(
        json.dumps(json.loads(serializers.serialize("json", file_instances)), indent=4),
        file=open(output_filemetadata_file, "w"),
    )

    # get the File entries that corresponds to the request ID
    queryset = (
        File.objects.prefetch_related(
            Prefetch("filemetadata_set", queryset=FileMetadata.objects.select_related("file").order_by("-created_date"))
        )
        .order_by("file_name")
        .all()
    )
    queryset = queryset.filter(filemetadata__metadata__igoRequestId=requestID)
    print(json.dumps(json.loads(serializers.serialize("json", queryset)), indent=4), file=open(output_file_file, "w"))


def dump_run(**kwargs):
    """
    Dump re-loadable Django database fixtures for a Run entry and its associated input and output Port entries
    """
    runID = kwargs.pop("runID")
    output_run_file = "{}.run.json".format(runID)
    output_port_input_file = "{}.port.input.json".format(runID)
    output_port_output_file = "{}.port.output.json".format(runID)
    output_files_output_file = "{}.files.json".format(runID)
    output_samples_output_file = "{}.samples.json".format(runID)

    # get the parent Run instance
    run_instance = Run.objects.get(id=runID)
    print(
        json.dumps(json.loads(serializers.serialize("json", [run_instance])), indent=4), file=open(output_run_file, "w")
    )

    # get the Run input and output Port instances
    input_queryset = run_instance.port_set.filter(port_type=PortType.INPUT)
    print(
        json.dumps(json.loads(serializers.serialize("json", input_queryset.all())), indent=4),
        file=open(output_port_input_file, "w"),
    )

    output_queryset = run_instance.port_set.filter(port_type=PortType.OUTPUT)
    print(
        json.dumps(json.loads(serializers.serialize("json", output_queryset.all())), indent=4),
        file=open(output_port_output_file, "w"),
    )
    all_data = []
    all_samples = []
    for item in output_queryset:
        files = item.files.all()
        for single_file in files:
            filemetadata_instance = FileMetadata.objects.filter(file=single_file).last()
            file_data = json.loads(serializers.serialize("json", [single_file]))
            if filemetadata_instance:
                filemetadata_data = json.loads(serializers.serialize("json", [filemetadata_instance]))
                all_data.append(filemetadata_data[0])
            all_data.append(file_data[0])
            if single_file.sample:
                sample_data = json.loads(serializers.serialize("json", [single_file.sample]))
                all_samples.append(sample_data[0])
    for item in input_queryset:
        files = item.files.all()
        for single_file in files:
            filemetadata_instance = FileMetadata.objects.filter(file=single_file).last()
            file_data = json.loads(serializers.serialize("json", [single_file]))
            if filemetadata_instance:
                filemetadata_data = json.loads(serializers.serialize("json", [filemetadata_instance]))
                all_data.append(filemetadata_data[0])
            all_data.append(file_data[0])
            if single_file.sample:
                sample_data = json.loads(serializers.serialize("json", [single_file.sample]))
                all_samples.append(sample_data[0])
    print(json.dumps(all_data, indent=4), file=open(output_files_output_file, "w"))
    sample_ids = []
    all_samples_unique = []
    for single_sample in all_samples:
        single_sample_id = single_sample["pk"]
        if single_sample_id not in sample_ids:
            all_samples_unique.append(single_sample)
            sample_ids.append(single_sample_id)
    print(json.dumps(all_samples_unique, indent=4), file=open(output_samples_output_file, "w"))


def dump_port_files(**kwargs):
    """ """
    portID = kwargs.pop("portID")
    output_port_file = "{}.port.json".format(portID)
    output_port_file_file = "{}.port.file.json".format(portID)
    output_port_filemetadat_file = "{}.port.filemetadat.json".format(portID)

    port_instance = Port.objects.get(id=portID)
    print(
        json.dumps(json.loads(serializers.serialize("json", [port_instance])), indent=4),
        file=open(output_port_file, "w"),
    )

    files_queryset = port_instance.files.all()
    print(
        json.dumps(json.loads(serializers.serialize("json", files_queryset.all())), indent=4),
        file=open(output_port_file_file, "w"),
    )

    filemetadata_queryset = FileMetadata.objects.filter(file__in=[i for i in files_queryset])
    print(
        json.dumps(json.loads(serializers.serialize("json", filemetadata_queryset.all())), indent=4),
        file=open(output_port_filemetadat_file, "w"),
    )


def dump_pipeline(**kwargs):
    """
    Dump re-loadable Django database fixtures for Pipeline entries and related table fixtures
    """
    pipelineName = kwargs.pop("pipelineName")
    output_pipeline_file = "{}.pipeline.json".format(pipelineName)
    output_pipeline_filegroup_file = "{}.pipeline.output_file_group.json".format(pipelineName)

    pipeline_instance = Pipeline.objects.get(name=pipelineName)
    print(
        json.dumps(json.loads(serializers.serialize("json", [pipeline_instance])), indent=4),
        file=open(output_pipeline_file, "w"),
    )

    print(
        json.dumps(json.loads(serializers.serialize("json", [pipeline_instance.output_file_group])), indent=4),
        file=open(output_pipeline_filegroup_file, "w"),
    )


def get_files(value, type):
    """
    Get a file from the database by its Beagle ID or filename
    """
    instances = []
    if type == "bid":
        instances.append(File.objects.get(id=value))
    if type == "filename":
        for item in File.objects.filter(file_name=value):
            instances.append(item)
    for instance in instances:
        yield (instance)


def dump_file(**kwargs):
    """
    Dump re-loadable Django database fixtures for File and FileMetadata items
    """
    bids = kwargs.pop("bids")
    onefile = kwargs.pop("onefile")
    filenames = kwargs.pop("filenames")
    filepaths = kwargs.pop("filepaths")
    get_key = "bid"
    if filenames == True:
        get_key = "filename"
    if filepaths == True:
        get_key = "path"

    all_data = []
    for bid in bids:
        output_label = bid
        if "/" in output_label:
            output_label = output_label.replace("/", ".")

        output_file_file = "{}.file.json".format(output_label)
        output_filemetadata_file = "{}.filemetadata.json".format(output_label)

        # get File entries that match the request ID
        for file_instance in get_files(value=bid, type=get_key):
            file_data = json.loads(serializers.serialize("json", [file_instance]))
            if onefile == False:
                print(json.dumps(file_data, indent=4), file=open(output_filemetadata_file, "w"))

            # get the FileMetadata entries that corresponds to the File
            filemetadata_instance = FileMetadata.objects.get(file=file_instance)
            filemetadata_data = json.loads(serializers.serialize("json", [filemetadata_instance]))
            if onefile == False:
                print(json.dumps(filemetadata_data, indent=4), file=open(output_file_file, "w"))

            if onefile == True:
                for item in file_data:
                    all_data.append(item)
                for item in filemetadata_data:
                    all_data.append(item)
    if onefile == True:
        output_file = "all.file_filemetadata.json"
        print(json.dumps(all_data, indent=4), file=open(output_file, "w"))


def parse():
    """
    Parses script args
    """
    parser = argparse.ArgumentParser(description="Dump items from Beagle database into a fixture-ready format")
    subparsers = parser.add_subparsers(help="Sub-commands available")

    # subparser for dumping requests
    request = subparsers.add_parser("request", help="Dump File and FileMetadata based on a requestId")
    request.add_argument("requestID", help="requestID to dump items for")
    request.set_defaults(func=dump_request)

    run = subparsers.add_parser("run", help="Dump output data for pipeline run")
    run.add_argument("runID", help="Run ID to dump items for")
    run.set_defaults(func=dump_run)

    pipeline = subparsers.add_parser("pipeline", help="Dump pipeline fixture")
    pipeline.add_argument("pipelineName", help="Name of the pipeline to dump")
    pipeline.set_defaults(func=dump_pipeline)

    file = subparsers.add_parser("file", help="Dump file fixture")
    file.add_argument("bids", nargs="*", help="Beagle db id's of the file to dump")
    file.add_argument("--onefile", action="store_true", help="Put all the outputs into a single file ")
    file.add_argument(
        "--filenames", action="store_true", help="Items passed are file basenames instead of Beagle db IDs "
    )
    file.add_argument("--filepaths", action="store_true", help="Items passed are file paths instead of Beagle db IDs ")
    file.set_defaults(func=dump_file)

    port_files = subparsers.add_parser("port_files", help="Dump port.files fixture")
    port_files.add_argument("portID", help="Port ID to dump files for")
    port_files.set_defaults(func=dump_port_files)

    args = parser.parse_args()
    args.func(**vars(args))


if __name__ == "__main__":
    parse()
