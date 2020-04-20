from notifier.event_handler.event import Event


class ETLGenericEvent(Event):

    def __init__(self, job_group, msg):
        self.job_group = job_group
        self.msg = msg

    @classmethod
    def get_type(cls):
        return "ETLGenericEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_generic_event"

    def __str__(self):
        return self.msg
