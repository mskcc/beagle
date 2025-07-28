import copy
import os
import csv
import logging
from django.db.models import Q
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.models import Pipeline
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File
from runner.models import Port, RunStatus
from file_system.models import FileMetadata
from runner.models import RunStatus, Port, Run
import json
from file_system.models import File, FileGroup, FileType

WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)

REFERENCE_FILEGROUP = "Microbiome References"
INPUT_FILEGROUP = "Microbiome Inputs"
# File group for input and reference


def _create_file_object(file):
    """
    Util function to create a simple CWL File object from a bam with a path attribute

    :param bam:
    :return:
    """
    return {"class": "File", "location": "iris://" + file}


class TaxProfilerOperator(Operator):
    def get_input(self):
        inputs = []
        sample_map = {}
        resource_filegroup = FileGroup.objects.get(name=INPUT_FILEGROUP)
        sample_files = File.objects.filter(file_group=resource_filegroup, metadata__project=self.request_id)
        for sample_input in sample_files:
            sample = sample_input.metadata["sample"]
            if sample not in sample_map:
                sample_map[sample] = {
                    "sample": sample,
                    "run_accession": sample_input.metadata["run_accession"],
                    "instrument_platform": sample_input.metadata["instrument_platform"],
                    "fastq_1": "",
                    "fastq_2": "",
                    "fasta": "",
                }
            sample_type = sample_input.metadata["type"]
            if sample_input == "R1":
                sample_map[sample]["fastq_1"] = _create_file_object(sample_input.path)
            elif sample_input == "R2":
                sample_map[sample]["fastq_2"] = _create_file_object(sample_input.path)
            elif sample_input == "fasta":
                sample_map[sample]["fasta"] = _create_file_object(sample_input.path)
        for single_sample in sample_map.values():
            inputs.append(single_sample)
        return inputs

    def get_database(self):
        databases = []
        resource_filegroup = FileGroup.objects.get(name=REFERENCE_FILEGROUP)
        database_files = File.objects.filter(file_group=resource_filegroup, metadata__type="database_sheet")
        for single_database in database_files:
            databases.append(
                {
                    "tool": single_database.metadata["tool"],
                    "db_name": single_database.metadata["db_name"],
                    "db_params": single_database.metadata["db_params"],
                    "db_path": _create_file_object(single_database.path),
                }
            )
            if single_database.metadata["tool"] == "kraken2":
                databases.append(
                    {
                        "tool": "bracken",
                        "db_name": "db1",
                        "db_params": ";-r 150",
                        "db_path": _create_file_object(single_database.path),
                    }
                )
        return databases

    def get_human_reference(self):
        resource_filegroup = FileGroup.objects.get(name=REFERENCE_FILEGROUP)
        human_reference_file = File.object.get(file_group=resource_filegroup, metadata__type="human_reference")
        return _create_file_object(human_reference_file.path)

    def get_jobs(self):
        """
        get_job information tor run NucleoVar Pipeline
        - self: NucleoVarOperator(Operator)

        :return: return RunCreator Objects with NucleoVar information
        """
        # Run Information
        LOGGER.info("Operator JobGroupNotifer ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")

        # Files
        inputs = self.get_input()
        databases = self.get_database()
        # Build Ridgeback Jobs from Sample Info
        input_json = {
            "input": inputs,
            "databases": databases,
            "run_metaphlan": True,
            "perform_shortread_hostremoval": True,
            "perform_shortread_qc": True,
            "perform_shortread_complexityfilter": True,
            "hostremoval_reference": self.get_human_reference(),
        }
        job_tags = {
            "pipeline": pipeline.name,
            "pipeline_version": pipeline.version,
        }
        job_json = {
            "name": "Taxprofiler: {run_date}".format(run_date=run_date),
            "app": app,
            "inputs": input_json,
            "tags": job_tags,
            "output_metadata": {},
        }
        print(job_json)
        return [RunCreator(**job_json)]
