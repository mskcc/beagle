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
LOGGER = logging.getLogger(__name__)

class DelphiOperator(Operator):
    def get_jobs(self):
        """
        Load paired sample data into a jsons that can be submitted to
        the nextflow pipeline, and then submit them as jobs through the
        RunCreator
        """

        request_id = self.request_id

        MAPPING_FILE = os.path.join(WORKDIR, "data", request_id, "input.csv")
        PAIRING_FILE = os.path.join(WORKDIR, "data", request_id, "pairs.csv")

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        output_directory_base = pipeline.output_directory
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        output_directory = os.path.join(
                output_directory_base, "chaos", request_id, jg_created_date
        )

        delphi_inputs = dict()
        delphi_inputs["name"] = "%s Tempo/Chronos Run" % request_id
        delphi_inputs["app"] = self.get_pipeline_id()
        delphi_inputs["tags"] = dict()
        delphi_inputs["output_metadata"] = dict()
        delphi_inputs["output_directory"] = output_directory
        inputs = dict()
        inputs["mapping"] = list()
        inputs["pairing"] = list()
        inputs["somatic"] = True
        inputs["aggregate"] = True

        header_m, data_mapping = get_data_from_file(MAPPING_FILE)
        for row in data_mapping:
            current_sample = dict()
            current_sample["assay"] = "exome"
            current_sample["target"] = "agilent"
            current_sample["sample"] = row["sample"]
            current_sample["fastq_pe1"] = {"class": "File", "location": "juno://" + row["R1"]}
            current_sample["fastq_pe2"] = {"class": "File", "location": "juno://" + row["R2"]}
            current_sample["num_fq_pairs"] = 1
            inputs["mapping"].append(current_sample)

        header_p, data_pairs = get_data_from_file(PAIRING_FILE)
        for row in data_pairs:
            current_pair = dict()
            current_pair["tumor"] = row["tumor"]
            current_pair["normal"] = row["normal"]
            inputs["pairing"].append(current_pair)

        delphi_inputs["inputs"] = inputs

        jobs = [delphi_inputs]

        return [RunCreator(**job) for job in jobs]
