import shutil
import logging
from django.conf import settings
from runner.models import Pipeline
from runner.models import Run
from runner.operator.operator import Operator

LOGGER = logging.getLogger(__name__)


class ChronosCopyOutputOperatorV2(Operator):
    CHRONOS_NAME = "chronos"
    CHRONOS_VERSION = "0.1.0"

    def get_jobs(self):
        jobs = []
        pipeline = Pipeline.objects.get(id=self.get_pipeline_id())
        destination_directory = Pipeline.objects.get(id=self.get_pipeline_id()).output_directory
        for run_id in self.run_ids:
            LOGGER.info(f"Copy outputs for {run_id} for {destination_directory}")
            run = Run.objects.get(id=run_id)
            output_file_group = str(pipeline.output_file_group.id)
            metadata = self.construct_metadata(run)
            name = f"Tempo Copy Output ({run.tags['ciTag']})"
            input_json = {
                "cmo_sample_name": run.tags["ciTag"],
                "src": run.output_directory,
                "dst": destination_directory,
                "result_dir": destination_directory,
            }
            job_json = {
                "name": name,
                "app": str(pipeline.id),
                "inputs": input_json,
                "tags": run.tags,
                "output_directory": destination_directory,
                "output_metadata": metadata,
            }
            jobs.append(job_json)
        return jobs

    def construct_metadata(self, run):
        metadata = run.tags
        if not all(k in run.tags for k in (settings.REQUEST_ID_METADATA_KEY, settings.SAMPLE_ID_METADATA_KEY)):
            sample = run.samples.first()
            metadata[settings.REQUEST_ID_METADATA_KEY] = sample.request_id
            metadata[settings.SAMPLE_ID_METADATA_KEY] = sample.sample_id
        return metadata
