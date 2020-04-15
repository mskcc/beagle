from notifier.event_handler.event import Event


class SetCIReviewEvent(Event):

    def __init__(self, job_group):
        self.job_group = job_group

    @classmethod
    def get_type(cls):
        return "SetCIReviewEvent"

    @classmethod
    def get_method(cls):
        return "process_transition_event"

    def __str__(self):
        return "CI Review Needed"
