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
from file_system.models import File, FileGroup, FileType
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline, Run
from .construct_copy_outputs import construct_copy_outputs_input, generate_sample_pairing_and_mapping_files, \
    get_output_directory_prefix


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
        mapping_file = self.write_to_file("sample_mapping.txt", mapping_file_content)
        pairing_file = self.write_to_file("sample_pairing.txt", pairing_file_content)
        data_clinical_file = self.write_to_file("sample_data_clinical.txt", data_clinical_content)

        input_json['meta'] = [
                mapping_file,
                pairing_file,
                data_clinical_file
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
                output_directory = os.path.join(pipeline.output_directory,
                                                "argos",
                                                output_prefix,
                                                argos_pipeline.version,
                                                jg_created_date)
            copy_outputs_job_data['output_directory'] = output_directory
        copy_outputs_job = [(APIRunCreateSerializer(
            data=copy_outputs_job_data), input_json)]

        return copy_outputs_job

    def write_to_file(self,fname,s):
        """
        Writes file to temporary location, then registers it to the temp file group
        """
        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, fname)
        with open(output, "w+") as fh:
            fh.write(s)
        os.chmod(output, 0o777)
        self.register_tmp_file(output)
        return {'class': 'File', 'location': "juno://" + output }

    def register_tmp_file(self, path):
        fname = os.path.basename(path)
        temp_file_group = FileGroup.objects.get(slug="temp")
        file_type = FileType.objects.get(name="txt")
        try:
            File.objects.get(path=path)
        except:
            print("Registering temp file %s" % path)
            f = File(file_name=fname,
                    path=path,
                    file_type=file_type,
                    file_group=temp_file_group)
            f.save()
