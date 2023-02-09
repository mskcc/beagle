from notifier.event_handler.event import Event


class VoyagerIsProcessingWholeRequestEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id

    @classmethod
    def get_type(cls):
        return "VoyagerIsProcessingWholeRequestEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        """
        TODO: Fill the content of the email
        :return: email body
        """
        body = f"We have received the request to run {self.request_id}. Please review this information carefully if this is not what you expected contact us. Results can be expected in 10-14 days."
        return body
