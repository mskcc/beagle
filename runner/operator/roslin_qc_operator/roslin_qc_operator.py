from runner.operator.operator import Operator
from runner.models import Run, Pipeline, Run,  RunStatus
from runner.serializers import APIRunCreateSerializer
from .bin import input
import datetime

class RoslinQcOperator(Operator):
    """
    Operator for Roslin QC pipeline
    """

    def __init__(self, model, request_id = None, run_ids = None):
        self.run_ids = run_ids
        self.runs = None
        if self.run_ids != None:
            self.runs = Run.objects.filter(id__in = self.run_ids)
        # TODO: add support for things like FileMetadata's
        # TODO: add support for multiple request ids

        Operator.__init__(self, model, request_id = request_id, run_ids = run_ids)

    def get_pipeline_id(self):
        return "9b7f2ac8-03a5-4c44-ae87-1d9f6500d19a"

    def get_input_data(self):
        """
        Build up the data to use for input to QC pipeline
        Needs to match the datastructure expected by the CWL pipeline input

        TODO: fill this in with handling of more types of input criteria; runs, requests, FileMetadata's, etc
        """
        input_data = {}
        if self.runs != None:
            input_data = input.build_inputs_from_runs(self.runs)
        # TODO: add methods here to add data from other items like requests, FileMetadata, etc
        return(input_data)

    def get_output_metadata(self):
        """
        Implement methods here to generate output metadata values that might need to be passed
        """
        return({})

    def get_data_for_serializer(self, input_data, output_metadata, create_date = None, name = None, tags = None, pipeline_id = None):
        """
        Put together the data that will be sent to the serializer for run creation
        """
        if create_date == None:
            create_date = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        if name == None:
            name = "Roslin QC {create_date}".format(create_date = create_date)

        if tags == None:
            tags = {}
            if self.request_id:
                tags['request_id'] = self.request_id
            if self.run_ids:
                tags['run_ids'] = self.run_ids

        if pipeline_id == None:
            pipeline_id = self.get_pipeline_id()

        serializer_data = {
            'app': pipeline_id,
            'inputs': input_data,
            'name': name,
            'tags': tags,
            'output_metadata': output_metadata
            }
        return(serializer_data)

    def get_jobs(self):
        input_data = self.get_input_data()
        output_metadata = self.get_output_metadata()
        serializer_data = self.get_data_for_serializer(input_data, output_metadata)
        run = APIRunCreateSerializer(data = serializer_data)
        return([(run, input_data)])
