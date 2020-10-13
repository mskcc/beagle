from django.conf import settings
from notifier.event_handler.event import Event


class OnlyNormalSamplesEvent(Event):

    def __init__(self, job_notifier, request_id):
        self.job_notifier = job_notifier
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "OnlyNormalSamplesEvent"

    @classmethod
    def get_method(cls):
        return "process_only_normal_samples_event"

    def __str__(self):
        TEMPLATE = """
        {cc}. Request {request_id} contains only normal samples.
        """
        return TEMPLATE.format(request_id=self.request_id, cc=settings.NOTIFIER_CC)
