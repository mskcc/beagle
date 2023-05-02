from notifier.event_handler.event import Event


class VoyagerActionRequiredForRunningEvent(Event):
    def __init__(self, job_notifier, email_to, email_from, subject, request_id, gene_panel, number_of_samples):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.gene_panel = gene_panel
        self.number_of_samples = number_of_samples

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
        body = f"""We have received the request to run {self.request_id} (Gene Panel: {self.gene_panel}; {self.number_of_samples} samples)<br>
        but are unable to proceed due to missing or incomplete data.

Please review your data and contact us to resubmit.<br>
<br>
Thank you,<br>
Nicholas D. Socci<br>
Director, Bioinformatics Core<br>
zzPDL_CMO_Pipeline_Support@mskcc.org<br>
"""
        return body
