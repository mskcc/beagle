from notifier.event_handler.event import Event


class SetPipelineFieldEvent(Event):

    def __init__(self, job_notifier, pipeline_name):
        self.job_notifier = job_notifier
        self.pipeline_name = pipeline_name

    @classmethod
    def get_type(cls):
        return "SetPipelineFieldEvent"

    @classmethod
    def get_method(cls):
        return "process_set_pipeline_field_event"

    def __str__(self):
        return self.pipeline_name
