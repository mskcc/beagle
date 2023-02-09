from notifier.event_handler.event import Event


class VoyagerIsProcessingPartialRequestEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id, unpaired):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.unpaired = unpaired

    @classmethod
    def get_type(cls):
        return "VoyagerIsProcessingPartialRequestEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        """
        :return: email body
        """
        body = f"""
Project specific voyager details:

Project 12405_F is partially running. Samples unpaired: {", ".join(self.unpaired)}
"""
        return body
