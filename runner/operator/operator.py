import logging
from file_system.models import File, FileMetadata
from runner.serializers import OperatorErrorSerializer, APIRunCreateSerializer
from django.db.models import Prefetch


class Operator(object):
    logger = logging.getLogger(__name__)

    def __init__(self, operator_name, request_id):
        self.pipeline_id = self.get_pipeline_id()
        self.operator = operator_name
        self.request_id = request_id
        self.files = File.objects.prefetch_related(
            Prefetch('filemetadata_set', queryset=
            FileMetadata.objects.select_related('file').order_by('-created_date'))).\
            order_by('file_name')
        self._jobs = []

    def get_pipeline_id(self):
        '''

        :return: PipelineId
        '''
        raise Exception("Implement this")

    def get_jobs(self):
        '''

        :return: ([`(APIRunCreateSerializer, job)`])
        '''
        return self._jobs

    def failed_to_create_job(self, error):
        operator_error = OperatorErrorSerializer(
            data={'operator_name': self.operator, 'request_id': self.request_id, 'error': error})
        if operator_error.is_valid():
            operator_error.save()
            self.logger.info('Operator: %s failed to create a job for request_id: %s with error: %s' % (
                self.operator, self.request_id, str(error)))
        else:
            self.logger.error('Invalid Operator: %s error' % self.operator)

    def ready_job(self, pipeline, tempo_inputs, job):
        self._jobs.append((APIRunCreateSerializer(data={'app': pipeline, 'inputs': tempo_inputs}), job))

