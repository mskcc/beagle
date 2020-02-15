#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to use for creating a modified, non-conflicting duplicate of an existing database fixture
Use this after you have dumped some fixtures to a .json file using `dump_db_fixtures.py`, and now you
want another fixture set that has different UUIDs and identifiers so you can load both at once in a dev database
in order to get work done with them.

Input: .json file produced by dump_db_fixtures.py

Output: a new .json file with updated key values

Usage
-----
    ./duplicate_fixtures.py ca18b090-03ad-4bef-acd3-52600f8e62eb.run.full.json

Notes
-----
The input .json file must have been produced with 'indent = 4' or have equivalent indenting, or this script will probably not work
"""
import sys
import json
import uuid
import copy
import re
import time

def get_unique_id():
    """
    Get a unique ID
    maybe replace with with uuid4?
    uuid1 has a lower chance of duplicate id's being generated

    TODO: see what Sinisa thinks about this later
    """
    return(uuid.uuid1())

def replace_primary_keys(input_file):
    """
    Replaces all primary keys in the file with new values
    """
    # get all primary keys that need to be changed
    all_pk = []
    with open(input_file) as f:
        for item in json.load(f):
            all_pk.append(item['pk'])

    # sort unique based on descending length
    # this makes sure we replace the longer pattern first in the next steps
    all_pk = sorted(list(set(all_pk)), key = len, reverse=True)

    # load all lines of text from the file
    lines = open(input_file).readlines()

    # make a copy for editing
    output_lines = copy.deepcopy(lines)

    editted_lines = []

    # search for every primary key in every line of text ... !! Yes, we are doing this
    for old_pk in all_pk:
        new_pk = str(get_unique_id())
        for i, old_line in enumerate(lines):
            if old_pk in old_line:
                # I think this only replaces first intance of the pattern? shouldnt matter for this if you printed JSON with indent = 4
                new_line = re.sub(old_pk, new_pk, output_lines[i])
                output_lines[i] = new_line

                # each line should only get editted one time doing this otherwise something is wrong
                if i not in editted_lines:
                    editted_lines.append(i)
                else:
                    print("ERROR: line {} is about to get editted twice; that is not supposed to happen something is wrong".format(i))
                    raise
    return(output_lines)

def get_field_values(input_lines, field_name):
    """
    Finds a list of all unique values for a given field in the file lines

    examples:

    "runId": "PITT_0390",
    >>> ["PITT_0390"]

    "requestId": "09670_D_1581808018",
    "sampleId": "09670_D_1",
    "patientId": "C-K2902H",
    "sampleName": "C-K2902H-P001-d",
    "externalSampleId": "S16-68609",
    "investigatorSampleId": "S16-68609",
    """
    all_values = set()
    search_pattern = '.*"{field_name}": "(.*)"'.format(field_name = field_name)
    for line in input_lines:
        match = re.search(search_pattern, line)
        if match != None:
            value = match.group(1)
            all_values.add(value)

    # return reverse sorted on length to ensure sub-patterns do not get replaced first later
    all_values = sorted(list(set(all_values)), key = len, reverse=True)
    return(all_values)

def replace_field_value(input_lines, field_name, old_value, new_value):
    """
    Replace the old value for a field with the new value in all file lines
    """
    # make a copy for editing
    output_lines = copy.deepcopy(input_lines)

    fieldname_search_pattern = '"{field_name}":'.format(field_name = field_name)

    # search for the field label in all lines and replace the value if found
    for i, line in enumerate(input_lines):
        # check that its a line with the desired field name in it
        line_match = re.search(fieldname_search_pattern, line)
        if line_match != None:
            # check that the desired value to be changed is present
            id_match = re.search(old_value, line)
            if id_match != None:
                # replace the old value with the new value
                new_line = re.sub(old_value, new_value, output_lines[i])
                output_lines[i] = new_line
    return(output_lines)

def main(input_file):
    """
    Main function for editing a fixtures file to replace all old primary keys with new keys
    So that both old and new fixtures sets can be loaded into the database at the same time
    """
    output_file_name = "{}.duplicated.json".format(input_file)

    # generate a timestamp string to use for new unique identifiers
    timestamp_str = str(int(time.time()))

    # replace all the primary keys with new values; need special handling for pk's because they do not always have a field label in the file
    output_lines = replace_primary_keys(input_file)

    # replace the values for all of these other desired fields; these fields are always clearly labeled in the file so they are easy to find
    for field_name in ['runId', 'requestId', 'sampleId', 'patientId', 'sampleName', 'externalSampleId', 'investigatorSampleId']:
        all_values = get_field_values(input_lines = output_lines, field_name = field_name)
        for old_value in all_values:
            # make a new value by appending the timestamp
            new_value = old_value + '_' + timestamp_str
            output_lines = replace_field_value(input_lines = output_lines, field_name = field_name, old_value = old_value, new_value = new_value)

    # save the output files
    with open(output_file_name, "w") as fout:
        fout.writelines(output_lines)

def parse():
    """
    Parses script args
    Script arg parsing will go here as this script grows
    """
    input_file = sys.argv[1]
    main(input_file)

if __name__ == '__main__':
    parse()
