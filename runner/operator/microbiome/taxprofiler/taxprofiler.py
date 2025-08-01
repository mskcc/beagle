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


def _create_file_object(file):
    """
    Util function to create a simple CWL File object from a bam with a path attribute

    :param bam:
    :return:
    """
    return {"class": "File", "location": "juno://" + file}


class TaxProfilerOperator(Operator):
    def get_input(self):
        inputs = []
        file_q = [
            "ERX5474930_ERR5766174_1.fa.gz",
            "ERX5474932_ERR5766176_2.fastq.gz",
            "ERX5474932_ERR5766176_1.fastq.gz",
        ]
        files = File.objects.filter(file_name__in=file_q)
        for f in files:
            if f.file_name.endswith("fa.gz"):
                inputs.append(
                    {
                        "sample": "2611",
                        "run_accession": "ERR5766174",
                        "instrument_platform": "ILLUMINA",
                        "fastq_1": "",
                        "fastq_2": "",
                        "fasta": _create_file_object(f.path),
                    }
                )

            if f.file_name.endswith("fastq.gz"):
                if f.file_name.endswith("_1.fastq.gz"):
                    fastqs = {
                        "sample": "2612",
                        "run_accession": "ERR5766176",
                        "instrument_platform": "ILLUMINA",
                        "fastq_1": _create_file_object(f.path),
                        "fastq_2": "",
                        "fasta": "",
                    }
                    for f2 in files:
                        if f.file_name.strip("_1.fastq.gz") == f2.file_name.strip("_2.fastq.gz"):
                            fastqs["fastq_2"] = _create_file_object(f2.path)
                    inputs.append(fastqs)
        return inputs

    def get_database(self):
        databases = []
        db_q = ["testdb-malt.tar.gz"]
        files = File.objects.filter(file_name__in=db_q)
        databases.append(
            {
                "tool": "malt",
                "db_name": "malt85",
                "db_params": "-id 85",
                "db_type": "short",
                "db_path": _create_file_object(files[0].path),
            }
        )
        return databases

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
        input_json = {"input": inputs, "databases": databases}
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
