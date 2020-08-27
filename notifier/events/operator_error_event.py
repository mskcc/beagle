from notifier.event_handler.event import Event


class OperatorErrorEvent(Event):

    def __init__(self, job_notifier, operator_run_id, sample_id, pipeline, error):
        self.job_notifier = job_notifier
        self.operator_run_id = operator_run_id
        self.sample_id = sample_id
        self.pipeline = pipeline
        self.error = error


    @classmethod
    def get_type(cls):
        return "OperatorErrorEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_error_event"

    def __str__(self):
        OPERATOR_ERROR_TEMPLATE = """
        Operator Error {operator_run_id}
        
        Sample Id: {sample_id}
        Pipeline: {pipeline_name}
        Error: {error}

        """
        return OPERATOR_ERROR_TEMPLATE.format(operator_run_id=self.operator_run_id,
                                              sample_id=self.sample_id,
                                              pipeline_name=self.pipeline,
                                              error=self.error)
