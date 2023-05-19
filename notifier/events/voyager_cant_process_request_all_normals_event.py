from django.conf import settings
from notifier.event_handler.event import Event


class VoyagerCantProcessRequestAllNormalsEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id, samples):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.samples = samples

    @classmethod
    def get_type(cls):
        return "VoyagerCantProcessRequestAllNormalsEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        """
        :return: email body
        """
        body = f"""
                Project {self.request_id} can not be run because it contains only normal samples.<br>
                There were a total of {len(self.samples)} samples received with the following ids:<br>

        {"<br>".join(self.samples)}
        <br><br>
        Thank you,<br>
        Nicholas D. Socci<br>
        Director, Bioinformatics Core<br>
        {settings.CONTACT_EMAIL}<br>
        """
        return body
