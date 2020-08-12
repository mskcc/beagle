from django.conf import settings
from notifier.event_handler.event import Event


class CustomCaptureCCEvent(Event):

    def __init__(self, job_notifier, assay):
        self.job_notifier = job_notifier
        self.assay = assay

    @classmethod
    def get_type(cls):
        return "CustomCaptureCCEvent"

    @classmethod
    def get_method(cls):
        return "process_custom_capture_cc_event"

    def __str__(self):
        TEMPLATE = """
        Ticket in AdminHold because of the assay: {assay}. {cc}
        """
        return TEMPLATE.format(assay=self.assay, cc=settings.NOTIFIER_CC)
