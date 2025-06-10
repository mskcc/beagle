import io
import os
import shutil
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
            pipeline = Pipeline.objects.get(id=self.get_pipeline_id())
            output_file_group = str(pipeline.output_file_group.id)
            metadata = self.construct_metadata(run)
            self.copy_bams(run, destination_directory, output_file_group, metadata)
            count = 0
            while not self.check_for_bams(run, destination_directory) and count < 5:
                count += 1
                self.copy_bams(run, destination_directory, output_file_group, metadata)
            if not self.check_for_bams(run, destination_directory):
                ci_tag = run.tags.get(settings.CMO_SAMPLE_TAG_METADATA_KEY)
                raise Exception(f"Failed to copy bams for sample {ci_tag}")
            self.append_trace(run, destination_directory)
            self.append_bam_outputs(run, destination_directory)
            self.clean_up_source_directory(run)
        return []

    def construct_metadata(self, run):
        metadata = run.tags
        if not all(k in run.tags for k in (settings.REQUEST_ID_METADATA_KEY, settings.SAMPLE_ID_METADATA_KEY)):
            sample = run.samples.first()
            metadata[settings.REQUEST_ID_METADATA_KEY] = sample.request_id
            metadata[settings.SAMPLE_ID_METADATA_KEY] = sample.sample_id
        return metadata

    def recursive_copy(self, src, dst, output_file_group, metadata={}):
        for item in os.listdir(src):
            if os.path.isdir(os.path.join(src, item)):
                if not os.path.exists(os.path.join(dst, item)):
                    LOGGER.info(f"Creating directory {os.path.join(dst, item)}")
                    os.mkdir(os.path.join(dst, item))
                else:
                    LOGGER.info(f"Directory already exists {os.path.join(dst, item)}")
                self.recursive_copy(os.path.join(src, item), os.path.join(dst, item), output_file_group, metadata)
            else:
                LOGGER.info(f"Copying file {os.path.join(src, item)}")
                if not self._copy(os.path.join(src, item), os.path.join(dst, item), output_file_group, metadata):
                    LOGGER.info(f"Failed to copy file {os.path.join(src, item)}")

    def copy_bams(self, run, destination_directory, output_file_group, metadata={}):
        source_bam_directory = os.path.join(run.output_directory, "bams")
        destination_bam_directory = os.path.join(destination_directory, "bams")
        self.recursive_copy(source_bam_directory, destination_bam_directory, output_file_group, metadata)

    def check_for_bams(self, run, destination_directory):
        ci_tag = run.tags.get(settings.CMO_SAMPLE_TAG_METADATA_KEY)
        destination_bam_directory = os.path.join(destination_directory, "bams")
        bam_location = os.path.join(destination_bam_directory, ci_tag, f"{ci_tag}.bam")
        bai_location = os.path.join(destination_bam_directory, ci_tag, f"{ci_tag}.bam.bai")
        if os.path.exists(bam_location) and os.path.exists(bai_location):
            LOGGER.info(f"Outputs for {ci_tag} successfully copied")
            return True
        LOGGER.info(f"Failed to copy outputs for {ci_tag} into {destination_directory}. Retrying...")
        return False

    def _copy(self, src, dst, output_file_group, metadata):
        ret = subprocess.call(f"cp {src} {dst}", shell=True)
        if ret == 0:
            path = f"iris://{dst}"
            size = os.path.getsize(dst)
            checksum = sha1(dst)
            request_id = metadata[settings.REQUEST_ID_METADATA_KEY]
            sample_id = metadata[settings.SAMPLE_ID_METADATA_KEY]
            FileProcessor.create_file_obj(path, size, checksum, output_file_group, metadata, request_id, [sample_id])
            return True
        else:
            return False

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
        # Read result bam file
        with open(bam_outputs_file_global, "r") as f:
            results = f.readlines()
            results = [line.rstrip() for line in results]
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
            line = "\t".join(elements)
            if line not in results:
                trace_file_result.append(line)
            else:
                LOGGER.warning(f"{line} already in {bam_outputs_file_global}")
        with io.open(bam_outputs_file_global, "a") as f:
            f.writelines(trace_file_result)

    def clean_up_source_directory(self, run):
        try:
            shutil.rmtree(run.output_directory)
        except Exception as e:
            logging.error(f"Failed to remove directory {run.output_directory}. {e}")
