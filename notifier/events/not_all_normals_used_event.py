from django.conf import settings
from notifier.event_handler.event import Event


class NotAllNormalsUsedEvent(Event):
    def __init__(self, job_notifier, request_id):
        self.job_notifier = job_notifier
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "NotAllNormalsUsedEvent"

    @classmethod
    def get_method(cls):
        return "process_not_all_normals_used_event"

    def __str__(self):
        TEMPLATE = """
        Not all normals are used for request {request_id}.
        """
        return TEMPLATE.format(request_id=self.request_id)
