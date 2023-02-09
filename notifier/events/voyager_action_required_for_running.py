from notifier.event_handler.event import Event


class VoyagerActionRequiredForRunningEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "VoyagerActionRequiredForRunningEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        """
        :return: email body
        """
        body = f"""
We have received the request to run {self.request_id}. You need to contact us with the necessary information before your project will be processed.
"""
        return body
