from file_system.models import File, FileMetadata
from django.db.models import Prefetch


class Operator(object):

    def __init__(self, request_id):
        self.pipeline_id = self.get_pipeline_id()
        self.request_id = request_id
        self.files = File.objects.prefetch_related(
            Prefetch('filemetadata_set', queryset=
            FileMetadata.objects.select_related('file').order_by('-created_date'))).\
            order_by('file_name')

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
    pass
