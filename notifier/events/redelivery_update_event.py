from notifier.event_handler.event import Event


class RedeliveryUpdateEvent(Event):

    def __init__(self, job_notifier, update):
        self.job_notifier = job_notifier
        self.update = update

    @classmethod
    def get_type(cls):
        return "RedeliveryUpdateEvent"

    @classmethod
    def get_method(cls):
        return "process_redelivery_update_event"

    def __str__(self):
        return self.update
