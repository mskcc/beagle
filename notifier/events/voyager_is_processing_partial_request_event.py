from notifier.event_handler.event import Event


class VoyagerIsProcessingPartialRequestEvent(Event):
    def __init__(
        self, job_notifier, email_to, email_from, subject, request_id, gene_panel, number_of_samples, unpaired
    ):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.gene_panel = gene_panel
        self.number_of_samples = number_of_samples
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
\n
Project {self.request_id} (Gene Panel: {self.gene_panel}; {self.number_of_samples} samples) is partially running.
\n
Samples unpaired: {", ".join(self.unpaired)}
"""
        return body
