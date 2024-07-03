from notifier.event_handler.event import Event


class ErrorImportingFilesEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id, msg):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.msg = msg

    @classmethod
    def get_type(cls):
        return "ErrorImportingFilesEvent"

    @classmethod
    def get_method(cls):
        return "process_send_email_event"

    def __str__(self):
        """
        :return: email body
        """
        body = f"""
                ERROR Importing Files received from SMILE
                <br>
                {self.msg}
        """
        return body
