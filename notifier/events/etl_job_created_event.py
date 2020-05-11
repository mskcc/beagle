from django.conf import settings
from notifier.event_handler.event import Event


class ETLJobCreatedEvent(Event):

    def __init__(self, job_group_id, sample_id, request_id, request_metadata):
        self.job_group_id = job_group_id
        self.sample_id = sample_id
        self.request_id = request_id
        self.request_metadata = request_metadata

    @classmethod
    def get_type(cls):
        return "ETLJobCreatedEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_job_imported_event"

    def __str__(self):
        return "Sample: {}, Request: {}".format(self.sample_id, self.request_id)
