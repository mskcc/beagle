from notifier.event_handler.event import Event


class ETLJobFailedEvent(Event):

    def __init__(self, job_notifier, msg):
        self.job_notifier = job_notifier
        self.msg = msg

    @classmethod
    def get_type(cls):
        return "ETLJobFailedEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_job_failed_event"

    def __str__(self):
        return self.msg
