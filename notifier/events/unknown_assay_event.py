from django.conf import settings
from notifier.event_handler.event import Event


class UnknownAssayEvent(Event):
    def __init__(self, job_notifier, assay):
        self.job_notifier = job_notifier
        self.assay = assay

    @classmethod
    def get_type(cls):
        return "UnknownAssayEvent"

    @classmethod
    def get_method(cls):
        return "process_assay_event"

    def __str__(self):
        TEMPLATE = """
        Unrecognized assay {assay}.
        """
        return TEMPLATE.format(assay=self.assay)
