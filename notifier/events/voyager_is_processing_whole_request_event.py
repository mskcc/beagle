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
        body = f"""We have received the request to run {self.request_id} and will begin processing them soon. Results typically take 10-14 days to generate.

Please review this information carefully; if anything in this project is not what you expected, contact us and we'll be happy to help."""
        return body
