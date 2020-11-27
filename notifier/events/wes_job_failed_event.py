from django.conf import settings
from notifier.event_handler.event import Event


class WESJobFailedEvent(Event):

    def __init__(self, job_notifier, assay):
        self.job_notifier = job_notifier
        self.assay = assay

    @classmethod
    def get_type(cls):
        return "WESJobFailedEvent"

    @classmethod
    def get_method(cls):
        return "process_wes_job_failed_event"

    def __str__(self):
        TEMPLATE = """
        Failed to import all samples for {assay}. {cc}
        """
        return TEMPLATE.format(assay=self.assay, cc=settings.NOTIFIER_WES_CC)
