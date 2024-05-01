import io
import os
import logging
import subprocess
from runner.models import Pipeline
from runner.models import Run
from runner.operator.operator import Operator


LOGGER = logging.getLogger(__name__)


class ChronosCopyOutputOperator(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.1.0"

    def get_jobs(self):
        destination_directory = Pipeline.objects.get(id=self.get_pipeline_id()).output_directory
        for run_id in self.run_ids:
            LOGGER.info(f"Copy outputs for {run_id} for {destination_directory}")
            run = Run.objects.get(id=run_id)
            self.copy_bams(run, destination_directory)
            self.append_trace(run, destination_directory)
            self.append_bam_outputs(run, destination_directory)
        return []

    def copy_bams(self, run, destination_directory):
        source_bam_directory = os.path.join(run.output_directory, "bams")
        destination_bam_directory = os.path.join(destination_directory, "bams")
        for directory in os.listdir(source_bam_directory):
            self._hard_copy(
                os.path.join(source_bam_directory, directory), destination_bam_directory
            )

    def _hard_copy(self, src, dst):
        ret = subprocess.call(f'cp -lr {src} {dst}', shell=True)
        if ret != 0:
            LOGGER.error(f"Failed to copy {src}")

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
        with io.open(bam_outputs_file_global, "a") as f:
            f.writelines(trace_file_content)
