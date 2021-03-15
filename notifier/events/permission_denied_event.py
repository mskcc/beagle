from django.conf import settings
from notifier.event_handler.event import Event


class PermissionDeniedEvent(Event):

    def __init__(self, job_notifier, error, cc):
        self.job_notifier = job_notifier
        self.error = error
        self.cc = cc

    @classmethod
    def get_type(cls):
        return "OperatorRunEvent"

    @classmethod
    def get_method(cls):
        return "process_permission_denied_event"

    def __str__(self):
        return "{error} CC: {cc}".format(error=self.error, cc=self.cc)
