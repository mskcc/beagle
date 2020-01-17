#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to count the number of FileMetadata items in the database based on metadata values

For example, get the number of items for each request

Usage
-----

$ db_metrics.py <metadata_field>

example:

$ db_metrics.py requestId | sort -k2nr,2n

other examples:

$ db_metrics.py tumorOrNormal

$ db_metrics.py baitSet
"""
import os
import sys
import json
import django
from django.db.models import Prefetch
from django.core import serializers
from django.db.models import Count

# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from file_system.models import File, FileMetadata, FileGroup, FileType
sys.path.pop(0)

key = sys.argv[1]
metadata_key = 'metadata__{}'.format(key)

for item in FileMetadata.objects.all().values(metadata_key).annotate(total=Count(metadata_key)):
    print("{}\t{}".format(item[metadata_key], item['total']))
