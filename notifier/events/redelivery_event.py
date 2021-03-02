from notifier.event_handler.event import Event


class RedeliveryEvent(Event):

    def __init__(self, job_notifier):
        self.job_notifier = job_notifier

    @classmethod
    def get_type(cls):
        return "RedeliveryEvent"

    @classmethod
    def get_method(cls):
        return "process_redelivery_event"

    def __str__(self):
        return "redelivery"
