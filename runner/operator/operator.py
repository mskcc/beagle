from file_system.models import File, FileMetadata


class Operator(object):

    def __init__(self, request_id):
        self.pipeline_id = self.get_pipeline_id()
        self.request_id = request_id
        self.files = File.objects
        self.filemetadata = FileMetadata.objects

    def get_pipeline_id(self):
        '''

        :return: PipelineId
        '''
        raise Exception("Implement this")

    def get_jobs(self):
        '''

        :return: (`APIRunCreateSerializer`,)
        '''
        raise Exception("Implement this")


class OperatorFactory(object):

    def factory(pipeline, request_id):
        if pipeline:
            return TempoOperator(request_id)
        else:
            raise Exception("Invalid job")
    factory = staticmethod(factory)
