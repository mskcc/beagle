from django.conf import settings
from notifier.event_handler.event import Event


class SendEmailEvent(Event):

    def __init__(self, job_notifier, email_to, email_from, subject, content):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.content = content

    @classmethod
    def get_type(cls):
        return "SendEmailEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        return self.content
