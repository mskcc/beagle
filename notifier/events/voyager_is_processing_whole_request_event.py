from notifier.event_handler.event import Event


class VoyagerIsProcessingWholeRequestEvent(Event):
    def __init__(
        self,
        job_notifier,
        email_to,
        email_from,
        subject,
        request_id,
        gene_panel,
        number_of_samples,
        number_of_samples_recived,
        match_normal_cnt,
        pooled_normal_cnt,
    ):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.gene_panel = gene_panel
        self.number_of_samples = number_of_samples
        self.number_of_samples_recived = number_of_samples_recived
        self.match_normal_cnt = match_normal_cnt
        self.pooled_normal_cnt = pooled_normal_cnt

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
        body = f"""
CMO Informatics has received the request to run project {self.request_id} in the ARGOS pipeline.<br> 
Processing will begin soon. Results typically take 10-14 days to generate.<br>
Please review the project information below carefully and contact us if there are any discrepancies.<br>
<br>
Gene Panel: {self.gene_panel}<br>
Number of samples received: {self.number_of_samples_recived}<br>
Number of samples running: {self.number_of_samples}<br>
Samples Paired with Match normal: {self.match_normal_cnt}<br>
Samples Paired with Pooled normal: {self.pooled_normal_cnt}<br>
"""
        return body
