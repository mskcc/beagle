import uuid
from runner.operator.operator import Operator
from runner.serializers import APIRunCreateSerializer


class TempoOperator(Operator):

    def __init__(self, request_id):
        Operator.__init__(self, request_id)

    def get_pipeline_id(self):
        return "69c842e1-017a-45d8-9c1f-1c3a99fc9d3b" # Return ID of the pipeline

    def get_jobs(self):
        files = self.files.filter(filemetadata__metadata__request_id=self.request_id).all()
        inputs = {'class': "File", 'location': 'juno:///test/bla.txt'}
        return [APIRunCreateSerializer(data={'app': self.get_pipeline_id(), 'inputs': inputs})]
