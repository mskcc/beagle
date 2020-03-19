import logging
from file_system.models import File, FileMetadata
from runner.serializers import OperatorErrorSerializer, APIRunCreateSerializer
from django.db.models import Prefetch
from beagle_etl.models import Operator as OperatorModel


class Operator(object):
    logger = logging.getLogger(__name__)

    def __init__(self, model, request_id=None, run_ids=[]):
        if not isinstance(model, OperatorModel):
            raise Exception("Must pass an instance of beagle_etl.models.Operator")

        self.model = model
        self.request_id = request_id
        self.run_ids = run_ids
        self.files = File.objects.prefetch_related(
            Prefetch('filemetadata_set', queryset=
            FileMetadata.objects.select_related('file').order_by('-created_date'))).\
            order_by('file_name')
        self._jobs = []

    def get_pipeline_id(self):
        # TODO(aef) need some better heuristic when returning pipeline id. Probably best for this method
        # to return an array of ids for one-to-many generation
        return str(self.model.pipeline_set.last().pk)

    def get_jobs(self):
        '''

        :return: ([`(APIRunCreateSerializer, job)`])
        '''
        return self._jobs

    def get_output_metadata(self):
        '''
        Override this method to set proper metadata to output files
        :return: dict
        '''
        return {}

    def failed_to_create_job(self, error):
        operator_error = OperatorErrorSerializer(
            data={'operator_name': self.model.slug, 'request_id': self.request_id, 'error': error})
        if operator_error.is_valid():
            operator_error.save()
            self.logger.info('Operator: %s failed to create a job for request_id: %s with error: %s' % (
                self.model.slug, self.request_id, str(error)))
        else:
            self.logger.error('Invalid Operator: %s error' % self.model.slug)

    def ready_job(self, pipeline, tempo_inputs, job):
        self._jobs.append((APIRunCreateSerializer(data={'app': pipeline, 'inputs': tempo_inputs}), job))
