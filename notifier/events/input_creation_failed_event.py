from notifier.event_handler.event import Event


class InputCreationFailedEvent(Event):

    def __init__(self, message, job_group, request_id, sample_id):
        self.job_group = job_group
        self.request_id = request_id
        self.sample_id = sample_id
        self.message = message

    @classmethod
    def get_type(cls):
        return "InputCreationFailedEvent"

    @classmethod
    def get_method(cls):
        return "process_input_creation_failed_event"

    def __str__(self):
        return self.message
