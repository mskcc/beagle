"""
DelphiOperator

Constructs input JSON for the prototype delphi (Tempo) pipeline and then
submits them as runs
"""
import os
import uuid
from pathlib import Path
from django.conf import settings
from notifier.models import JobGroup
from file_system.models import File, FileGroup, FileType
from runner.models import Pipeline, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .bin.helpers import get_data_from_file, construct_delphi_input_jsons


class DelphiOperator(Operator):

    CSV_FILE = "data/input.csv"

    def get_jobs(self):
        """
        Load paired sample data into a jsons that can be submitted to
        the nextflow pipeline, and then submit them as jobs through the
        RunCreator
        """
        request_id = self.request_id
        data = get_data_from_file(CSV_FILE)
        delphi_inputs = construct_delphi_input_jsons(data)

        return [RunCreator(**job) for job in delphi_inputs]
