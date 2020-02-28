#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to mark a Beagle Run as "complete" using a pre-made JSON representing the CWL output
Use this by first creating a Run using;


curl -H "Content-Type: application/json" \
-X POST \
-H "Authorization: Bearer $$token" \
--data '{"request_ids":["$(REQID)"], "pipeline_name": "$(PIPELINE)"}' \
http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/request/

then, get the Run ID for the created Run (from Admin panel or other) and feed it the pre-made JSON output here to
populate all the Ports and Files for the run output
"""
import os
import sys
import django
import json

# import django app from parent dir
parentdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parentdir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "beagle.settings")
django.setup()
from runner.run.objects.run_object import RunObject
sys.path.pop(0)

run_id = sys.argv[1]
input_json = sys.argv[2]

cwl_output = json.load(open(input_json))
run_obj = RunObject.from_db(run_id = run_id)
run_obj.complete(outputs = cwl_output)
run_obj.to_db()
