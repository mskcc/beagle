from notifier.event_handler.event import Event


class RedeliveryEvent(Event):

    def __init__(self, job_group):
        self.job_group = job_group

    @classmethod
    def get_type(cls):
        return "RedeliveryEvent"

    @classmethod
    def get_method(cls):
        return "process_redelivery_event"

    def __str__(self):
        return "redelivery"
