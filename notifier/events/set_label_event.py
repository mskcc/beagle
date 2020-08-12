from notifier.event_handler.event import Event


class SetLabelEvent(Event):

    def __init__(self, job_notifier, label):
        self.job_notifier = job_notifier
        self.label = label

    @classmethod
    def get_type(cls):
        return "SetLabelEvent"

    @classmethod
    def get_method(cls):
        return "process_set_label_event"

    def __str__(self):
        return self.label
