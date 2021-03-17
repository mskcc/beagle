"""
Example Operator implementation
"""
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer
from runner.models import Pipeline
from file_system.models import FileMetadata

class DemoOperator(Operator):
    _pipeline_name = "demo" # use this to set as the Pipeline.name attribute in the db

    def create_input(self):
        """
        Make the CWL input data structure to run the pipeline job

        TODO: right now run_api_view does not support creating input directly from File.id; so need to use request_id, at some point just use File.id instead
        """
        file = FileMetadata.objects.filter(metadata__requestId = self.request_id).first().file
        data = {
            'input_file':{
                'class': 'File',
                'location': 'juno://' + file.path # NOTE: hard coded juno location here
            }
        }
        return(data)

    def get_pipeline_id(self):
        """
        Get the primary key for the Pipeline entry matching this operator
        For this particular Operator, the Pipeline.name field is saved under self._pipeline_name for convenience
        """
        pipeline_instance = Pipeline.objects.get(name = self._pipeline_name)
        return(pipeline_instance.id)

    def get_jobs(self):
        """
        Create job entries to pass to Ridgeback
        """
        pipeline_obj = Pipeline.objects.get(id=self.get_pipeline_id())
        inputs = self.create_input()
        name = "DEMO JOB"
        serialized_run = APIRunCreateSerializer(
            data = dict(app = pipeline_obj.id, inputs = inputs, name = name, tags = {})
        )
        job = inputs
        job = (serialized_run, job)
        jobs = [job]
        return(jobs)
