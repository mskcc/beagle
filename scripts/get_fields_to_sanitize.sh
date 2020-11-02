#!/bin/bash
set -euo pipefail

# script to get the fields from a FileMetadata JSON that need to be sanitized
# requires that the JSON is saved with 'indent = 4' or similar indentation

input_file="${1}"

grep -E 'sampleId|patientId|sampleName|externalSampleId|investigatorSampleId' "${input_file}" | tr -s ' ' | cut -d ':' -f2 | tr -d '"' | tr -d ',' | sed -e 's|^ ||g' | sort -u | awk '{print length($1), $0}' | sort -k 1,1nr | cut -d ' ' -f2-
