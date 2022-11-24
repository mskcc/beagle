"""
DelphiOperator

Constructs input JSON for the prototype delphi (Tempo) pipeline and then
submits them as runs
"""
import os
import uuid
import logging
from pathlib import Path
from django.conf import settings
from notifier.models import JobGroup
from file_system.models import File, FileGroup, FileType
from runner.models import Pipeline, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .bin.helpers import get_data_from_file

WORKDIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(WORKDIR, "data/input.csv")
LOGGER = logging.getLogger(__name__)


class DelphiOperator(Operator):
    def get_jobs(self):
        """
        Load paired sample data into a jsons that can be submitted to
        the nextflow pipeline, and then submit them as jobs through the
        RunCreator
        """
        request_id = self.request_id
        header, data = get_data_from_file(CSV_FILE)
        delphi_inputs = dict()
        delphi_inputs["name"] = "Delphi A Tempo/Chronos Run"
        delphi_inputs["app"] = self.get_pipeline_id()
        delphi_inputs["tags"] = dict()
        delphi_inputs["output_metadata"] = dict()
        delphi_inputs["output_directory"] = "/juno/work/ci/ops/delphiA"
        inputs = dict()
        inputs["somatic"] = True
        inputs["mapping"] = list()
        for row in data:
            current_sample = dict()
            current_sample["assay"] = "exome"
            current_sample["target"] = "impact505"
            current_sample["sample"] = row["sample"]
            current_sample["fastq_pe1"] = {"class": "File", "location": row["R1"]}
            current_sample["fastq_pe2"] = {"class": "File", "location": row["R2"]}
            inputs["mapping"].append(current_sample)
        delphi_inputs["inputs"] = inputs

        jobs = [delphi_inputs]

        return [RunCreator(**job) for job in jobs]
