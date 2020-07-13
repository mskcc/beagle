from notifier.event_handler.event import Event


class RedeliveryUpdateEvent(Event):

    def __init__(self, job_group, update):
        self.job_group = job_group
        self.update = update

    @classmethod
    def get_type(cls):
        return "RedeliveryUpdateEvent"

    @classmethod
    def get_method(cls):
        return "process_redelivery_update_event"

    def __str__(self):
        return self.update
