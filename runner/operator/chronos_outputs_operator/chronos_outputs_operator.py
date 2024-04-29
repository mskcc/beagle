import io
import os
from os.path import join, abspath
from django.conf import settings
from runner.models import Pipeline
from runner.models import Run
from runner.operator.operator import Operator


class ChronosOutputOperator(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.1.0"

    def get_jobs(self):
        destination_directory = Pipeline.objects.get(id=self.get_pipeline_id()).output_directory
        for run_id in self.run_ids:
            run = Run.objects.get(run_id)

    def copy_bams(self, run, destination_directory):
        source_bam_directory = os.path.join(run.output_directory, 'bams')
        destination_bam_directory = destination_directory
        for directory in os.listdir(source_bam_directory):
            self._hard_copy(os.path.join(source_bam_directory, directory),
                            os.path.join(destination_bam_directory, directory))

    def _hard_copy(self, src, dst):
        if not os.path.exists(dst):
            os.mkdir(dst)
        for root, dirs, files in os.walk(src):
            curdst = join(dst, root)
            for d in dirs:
                os.mkdir(join(curdst, d))
            for f in files:
                fromfile = join(root, f)
                to = join(curdst, f)
                os.link(fromfile, to)

    def append_trace(self, run, destination_directory):
        trace_file_path = os.path.join(run.output_directory, 'trace.txt')
        trace_file_global = os.path.join(destination_directory, 'trace.txt')
        with open(trace_file_path, 'r') as f:
            # Read trace file content without header
            trace_file_content = f.readlines()[1:]
        with io.open(trace_file_global, 'a') as f:
            f.writelines(trace_file_content)

    def append_bam_outputs(self, run, destination_directory):
        bam_outputs_path = os.path.join(run.output_directory, 'pipeline_output.csv')
        bam_outputs_file_global = os.path.join(destination_directory, 'pipeline_output.csv')
        with open(bam_outputs_path, 'r') as f:
            # Read trace file content without header
            trace_file_content = f.readlines()[1:]
        with io.open(bam_outputs_file_global, 'a') as f:
            f.writelines(trace_file_content)
