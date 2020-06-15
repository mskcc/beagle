"""
ArgosQcOperator

Constructs input JSON for the argos QC pipeline and then
submits them as runs
"""
import os
import logging
from notifier.models import JobGroup
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from .construct_argos_qc_outputs import construct_argos_qc_input
LOGGER = logging.getLogger(__name__)


class ArgosQcOperator(Operator):
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
        input_json = construct_argos_qc_input(run_ids)
        number_of_runs = len(run_ids)
        name = "ARGOS QC OUTPUTS %s runs [%s,..] " % (
            number_of_runs, run_ids[0])

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        pipeline_version = pipeline.version
        project_prefix = input_json['project_prefix']

        tags = {"tumor_sample_names": input_json['tumor_sample_names'],
                "normal_sample_names": input_json['normal_sample_names']}

        argos_qc_outputs_job_data = {
            'app': app,
            'inputs': input_json,
            'name': name,
            'notify_for_outputs': ['qc_pdf'],
            'tags': tags}

        """
        If project_prefix and job_group_id, write output to a directory
        that uses both
        """
        output_directory = None
        project_prefix = "test_project_prefix"
        print(project_prefix)
        if project_prefix:
            tags["project_prefix"] = project_prefix
            if self.job_group_id:
                jg = JobGroup.objects.get(id=job_group_id)
                jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
                output_directory = os.path.join(pipeline.output_directory,
                                                "argos",
                                                project_prefix,
                                                pipeline_version,
                                                jg_create_date)
                print(output_directory)

            argos_qc_outputs_job_data['output_directory'] = output_directory

        argos_qc_outputs_job = [(APIRunCreateSerializer(
            data=argos_qc_outputs_job_data), input_json)]

        return argos_qc_outputs_job
