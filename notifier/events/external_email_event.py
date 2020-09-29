from django.conf import settings
from notifier.event_handler.event import Event


class ExternalEmailEvent(Event):

    def __init__(self, job_notifier, request_id):
        self.job_notifier = job_notifier
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "ExternalEmailEvent"

    @classmethod
    def get_method(cls):
        return "process_external_email_event"

    def __str__(self):
        TEMPLATE = """
        {cc}. PI email is a non-MSK email. Determine if this is an external project and if so, obtain a PO.
        """
        return TEMPLATE.format(cc=settings.NOTIFIER_CC)
