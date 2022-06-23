from notifier.event_handler.event import Event


class VoyagerCantProcessRequestAllNormalsEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id

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
        body = "Project {igo_request_id} can't be run because it contains only normal samples.".format(
            igo_request_id=self.request_id
        )
        return body
