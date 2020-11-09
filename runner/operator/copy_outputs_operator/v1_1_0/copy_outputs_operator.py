"""
CopyOutputsOperator

Constructs input JSON for the copy outputs pipeline and then
submits them as runs
"""
import os
from notifier.models import JobGroup
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from .construct_copy_outputs import construct_copy_outputs_input, generate_sample_pairing_and_mapping_files, get_output_directory_prefix


class CopyOutputsOperator(Operator):
    """
    Constructs input JSON for the argos QC pipeline and then
    submits them as runs
    """
    def get_jobs(self):
        """
        From self, retrieve relevant run IDs, build the input JSON for
        the pipeline, and then submit them as jobs through the
        APIRunCreateSerializer
        """
        run_ids = self.run_ids
        input_json = construct_copy_outputs_input(run_ids)

        mapping_file_content, pairing_file_content, data_clinical_content = generate_sample_pairing_and_mapping_files(
            run_ids)

        input_json['meta'] = [
            {
                "class": "File",
                "basename": "sample_mapping.txt",
                "contents": mapping_file_content
            },
            {
                "class": "File",
                "basename": "sample_pairing.txt",
                "contents": pairing_file_content
            },
            {
                "class": "File",
                "basename": "sample_data_clinical.txt",
                "contents": data_clinical_content
            }
        ]

        number_of_runs = len(run_ids)
        name = "ARGOS COPY OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json['project_prefix']
        output_directory_prefix = get_output_directory_prefix(self.run_ids)

        tags = {"run_ids": run_ids}

        copy_outputs_job_data = {
            'app': app,
            'inputs': input_json,
            'name': name,
            'tags': tags
        }

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both
        """
        output_directory = None
        if project_prefix:
            tags["project_prefix"] = project_prefix
            if self.job_group_id:
                output_prefix = output_directory_prefix if output_directory_prefix else project_prefix
                jg = JobGroup.objects.get(id=self.job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(pipeline.output_directory,
                                                "argos",
                                                output_prefix,
                                                pipeline_version,
                                                jg_created_date)
            copy_outputs_job_data['output_directory'] = output_directory
        copy_outputs_job = [(APIRunCreateSerializer(
            data=copy_outputs_job_data), input_json)]

        return copy_outputs_job
