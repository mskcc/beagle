from notifier.event_handler.event import Event


class SetPipelineCompletedEvent(Event):

    def __init__(self, job_notifier):
        self.job_notifier = job_notifier

    @classmethod
    def get_type(cls):
        return "SetPipelineCompletedEvent"

    @classmethod
    def get_method(cls):
        return "process_transition_event"

    def __str__(self):
        return "Pipeline Completed; No Failures"
