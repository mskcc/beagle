from notifier.event_handler.event import Event


class OperatorRequestEvent(Event):

    def __init__(self, job_notifier, error):
        self.job_notifier = job_notifier
        self.error = error

    @classmethod
    def get_type(cls):
        return "OperatorRequestEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_request_event"

    def __str__(self):
        return self.error
