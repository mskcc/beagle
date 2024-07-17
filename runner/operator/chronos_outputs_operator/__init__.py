import io
import os
import logging
import subprocess

from django.conf import settings

from file_system.helper.checksum import sha1
from runner.models import Pipeline
from runner.models import Run
from runner.operator.operator import Operator
from runner.run.processors.file_processor import FileProcessor

LOGGER = logging.getLogger(__name__)


class ChronosCopyOutputOperator(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.1.0"

    def get_jobs(self):
        destination_directory = Pipeline.objects.get(id=self.get_pipeline_id()).output_directory
        for run_id in self.run_ids:
            LOGGER.info(f"Copy outputs for {run_id} for {destination_directory}")
            run = Run.objects.get(id=run_id)
            metadata = run.tags
            self.copy_bams(run, destination_directory, metadata)
            self.append_trace(run, destination_directory)
            self.append_bam_outputs(run, destination_directory)
        return []

    def recursive_copy(self, src, dst, metadata={}):
        for item in os.listdir(src):
            if os.path.isdir(os.path.join(src, item)):
                if not os.path.exists(os.path.join(dst, item)):
                    LOGGER.info(f"Creating directory {os.path.join(dst, item)}")
                    os.mkdir(os.path.join(dst, item))
                else:
                    LOGGER.info(f"Directory already exists {os.path.join(dst, item)}")
                self.recursive_copy(os.path.join(src, item), os.path.join(dst, item))
            else:
                LOGGER.info(f"Copying file {os.path.join(src, item)}")
                self._copy(os.path.join(src, item), os.path.join(dst, item), metadata)

    def copy_bams(self, run, destination_directory, metadata={}):
        source_bam_directory = os.path.join(run.output_directory, "bams")
        destination_bam_directory = os.path.join(destination_directory, "bams")
        self.recursive_copy(source_bam_directory, destination_bam_directory, metadata)

    def _copy(self, src, dst, metadata):
        ret = subprocess.call(f"cp {src} {dst}", shell=True)
        if ret != 0:
            LOGGER.error(f"Failed to copy {src}")
        else:
            path = f"juno://{dst}"
            size = os.path.getsize(dst)
            checksum = sha1(dst)
            request_id = metadata[settings.REQUEST_ID_METADATA_KEY]
            sample_id = metadata[settings.SAMPLE_ID_METADATA_KEY]
            FileProcessor.create_file_obj(path, size, checksum, self.file_group, metadata, request_id, [sample_id])

    def append_trace(self, run, destination_directory):
        trace_file_path = os.path.join(run.output_directory, "trace.txt")
        trace_file_global = os.path.join(destination_directory, "trace.txt")
        with open(trace_file_path, "r") as f:
            # Read trace file content without header
            trace_file_content = f.readlines()[1:]
        with io.open(trace_file_global, "a") as f:
            f.writelines(trace_file_content)

    def append_bam_outputs(self, run, destination_directory):
        bam_outputs_path = os.path.join(run.output_directory, "pipeline_output.csv")
        bam_outputs_file_global = os.path.join(destination_directory, "pipeline_output.csv")
        with open(bam_outputs_path, "r") as f:
            # Read output bam file content without header
            trace_file_content = f.readlines()[1:]
            trace_file_result = []
        for line in trace_file_content:
            elements = line.split("\t")
            file_name = elements[2].split("/")[-1]
            sample = elements[2].split("/")[-2]
            elements[2] = os.path.join(destination_directory, "bams", sample, file_name)
            file_name = elements[3].split("/")[-1]
            sample = elements[3].split("/")[-2]
            elements[3] = os.path.join(destination_directory, "bams", sample, file_name)
            trace_file_result.append("\t".join(elements))
        with io.open(bam_outputs_file_global, "a") as f:
            f.writelines(trace_file_result)
