#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to dump database entries for File and FileMetadata for a specific request
into a JSON format that can be re-loaded into the database later with the
`manage.py loaddata file.json` command
This makes it easier to generate database fixtures from pre-existing entires

Usage
-----

$ dump_request.py <requestId>

example:

$ dump_request.py 07951_AP

Output
------

- <requestId>.file.json

- <requestId>.filemetadata.json

"""
import os
import sys
import json
import django
from django.db.models import Prefetch
from django.core import serializers

# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from file_system.models import File, FileMetadata, FileGroup, FileType
sys.path.pop(0)

requestID = sys.argv[1]
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
