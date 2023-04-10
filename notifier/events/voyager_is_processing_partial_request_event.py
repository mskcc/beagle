from notifier.event_handler.event import Event


class VoyagerIsProcessingPartialRequestEvent(Event):
    def __init__(
        self,
        job_notifier,
        email_to,
        email_from,
        subject,
        request_id,
        gene_panel,
        number_of_samples,
        number_of_samples_received,
        match_normal_cnt,
        pooled_normal_cnt,
        unpaired,
    ):
        self.job_notifier = job_notifier
        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.request_id = request_id
        self.gene_panel = gene_panel
        self.number_of_samples = number_of_samples
        self.number_of_samples_received = number_of_samples_received
        self.match_normal_cnt = match_normal_cnt
        self.pooled_normal_cnt = pooled_normal_cnt
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
        CMO Informatics has received the request to run project {self.request_id} in the ARGOS pipeline. 
        Not all samples are being processed at this time. 
        Processing of valid samples will begin soon. Results typically take 10-14 days to generate. 
        Please review the project information below carefully and contact us to resolve issues with invalid samples.
        
Gene Panel: {self.gene_panel}
Number of samples received: {self.number_of_samples_received}
Number of samples running: {self.number_of_samples}
Samples Paired with Match normal: {self.match_normal_cnt}
Samples Paired with Pooled normal: {self.pooled_normal_cnt}

Samples with the following IDs are not being processed:
{",".join(self.unpaired)}
"""
        return body
