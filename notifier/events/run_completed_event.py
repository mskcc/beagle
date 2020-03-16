from notifier.event_handler.event import Event


class RunCompletedEvent(Event):

    def __init__(self, request_id, run_id, run_status):
        self.request_id = request_id
        self.run_id = run_id
        self.run_status = run_status

    @classmethod
    def get_type(cls):
        return "RunCompletedEvent"

    @classmethod
    def get_method(cls):
        return "process_run_completed"

    def __str__(self):
        return "Run %s status: %s" % (self.run_id, self.run_status)

