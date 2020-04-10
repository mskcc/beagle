from notifier.event_handler.event import Event


class TempoMPGenEvent(Event):

    def __init__(self, job_group, msg):
        self.job_group = job_group
        self.msg = msg

    @classmethod
    def get_type(cls):
        return "TempoMPGenEvent"

    @classmethod
    def get_method(cls):
        return "process_tempo_mpgen_event"

    def __str__(self):
        TEMPO_MSG_TEMPLATE = """
        {msg}
        """
        return TEMPO_MSG_TEMPLATE.format(msg=self.msg)
