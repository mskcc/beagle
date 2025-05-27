"""
CopyOutputsOperator

Constructs input JSON for the copy outputs pipeline and then
submits them as runs
"""

import os
import uuid
from pathlib import Path
from django.conf import settings
from notifier.models import JobGroup
from file_system.models import File, FileGroup
from file_system.serializers import CreateFileSerializer
from runner.models import Pipeline, Run
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from .construct_copy_outputs import (
    construct_copy_outputs_input,
    generate_sample_pairing_and_mapping_files,
    get_output_directory_prefix,
    get_project_prefix,
)


class CopyOutputsOperator(Operator):
    """
    Constructs input JSON for the argos QC pipeline and then
    submits them as runs
    """

    ARGOS_NAME = "argos"
    ARGOS_VERSION = "1.8.0"

    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        RunCreator
        """
        run_ids = self.run_ids
        input_json = construct_copy_outputs_input(run_ids)

        mapping_file_content, pairing_file_content, data_clinical_content = generate_sample_pairing_and_mapping_files(
            run_ids
        )

        number_of_runs = len(run_ids)
        name = "ARGOS COPY OUTPUTS %s runs [%s,..] " % (number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        project_prefix = input_json["project_prefix"]
        output_directory_prefix = get_output_directory_prefix(self.run_ids)

        mapping_file = self.write_to_file(
            "sample_mapping.txt", mapping_file_content, project_prefix, pipeline.name, pipeline.version
        )
        pairing_file = self.write_to_file(
            "sample_pairing.txt", pairing_file_content, project_prefix, pipeline.name, pipeline.version
        )
        data_clinical_file = self.write_to_file(
            "sample_data_clinical.txt", data_clinical_content, project_prefix, pipeline.name, pipeline.version
        )

        input_json["meta"] = [mapping_file, pairing_file, data_clinical_file]

        tags = {"run_ids": run_ids}
        log_directory = self.get_log_directory()
        copy_outputs_job_data = {
            "app": app,
            "inputs": input_json,
            "name": name,
            "tags": tags,
            "log_directory": log_directory,
        }

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both

        Also use argos version number for output instead of pipeline version
        that's listed in Beagle
        """

        argos_run = Run.objects.get(id=run_ids[0])
        argos_pipeline = argos_run.app

        output_directory = None
        if project_prefix:
            tags["project_prefix"] = project_prefix
            if self.job_group_id:
                output_prefix = output_directory_prefix if output_directory_prefix else project_prefix
                jg = JobGroup.objects.get(id=self.job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(
                    pipeline.output_directory, "argos", output_prefix, argos_pipeline.version, jg_created_date
                )
            copy_outputs_job_data["output_directory"] = output_directory

        copy_outputs_job = [RunCreator(**copy_outputs_job_data)]
        return copy_outputs_job

    def write_to_file(self, fname, s, project_prefix, pipeline_name, pipeline_version):
        """
        Writes file to temporary location, then registers it to the temp file group
        """
        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        self.register_tmp_file(output, project_prefix, pipeline_name, pipeline_version)
        return {"class": "File", "location": "iris://" + output}

    def register_tmp_file(self, path, project_prefix, pipeline_name, pipeline_version):
        fname = os.path.basename(path)
        temp_file_group_pk = FileGroup.objects.get(slug="temp").pk
        file_type = "txt"
        metadata = {"projectId": project_prefix, "pipelineName": pipeline_name, "pipelineVersion": pipeline_version}
        data = {"path": path, "file_type": file_type, "metadata": metadata, "file_group": temp_file_group_pk}
        try:
            File.objects.get(path=path)
        except:
            print("Registering temp file %s" % path)
            serializer = CreateFileSerializer(data=data)
            if serializer.is_valid():
                file = serializer.save()
            else:
                raise Exception("Failed to create temp file %s. Error %s" % (path, str(serializer.errors)))

    def get_log_directory(self):
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        log_directory_prefix = get_project_prefix(self.run_ids)
        log_directory = os.path.join(
            pipeline.log_directory,
            self.ARGOS_NAME,
            log_directory_prefix,
            self.ARGOS_VERSION,
            jg_created_date,
            "json",
            pipeline.name,
            pipeline.version,
        )
        return log_directory
