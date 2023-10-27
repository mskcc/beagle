from notifier.event_handler.event import Event


class OperatorErrorEvent(Event):
    def __init__(self, job_notifier, error):
        self.job_notifier = job_notifier
        self.error = error

    @classmethod
    def get_type(cls):
        return "OperatorErrorEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_error_event"

    def __str__(self):
        OPERATOR_ERROR_TEMPLATE = """
        Operator Error:
        
        Error: {error}
        """
        return OPERATOR_ERROR_TEMPLATE.format(
            error=self.error,
        )
