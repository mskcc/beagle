from django.conf import settings
from notifier.event_handler.event import Event


class RedeliveryEvent(Event):

    def __init__(self, job_group, request_id):
        self.job_group = job_group
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "RedeliveryEvent"

    @classmethod
    def get_method(cls):
        return "process_redelivery_event"

    def __str__(self):
        TEMPLATE = """
        RequestId is redelivered: {request_id}. {cc}
        """
        return TEMPLATE.format(request_id=self.request_id, cc=settings.REDELIVERY_CC)
