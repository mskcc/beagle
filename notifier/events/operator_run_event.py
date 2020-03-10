import json
from notifier.event_handler.event import Event


class OperatorRunEvent(Event):

    def __init__(self, request_id, valid_runs, pooled_normals):
        self.request_id = request_id
        self.valid_runs = valid_runs
        self.pooled_normals = pooled_normals

    @classmethod
    def get_type(cls):
        return "OperatorRunEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_run_event"

    def __str__(self):
        comment = "Runs submitted:\n"
        for r in self.valid_runs:
            comment += "%s\n" % r
        return comment
