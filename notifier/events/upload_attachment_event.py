from notifier.event_handler.event import Event


class UploadAttachmentEvent(Event):

    def __init__(self, job_group, file_name, content, download=False):
        self.job_group = job_group
        self.file_name = file_name
        self.content = content
        self.download = download

    @classmethod
    def get_type(cls):
        return "UploadAttachmentEvent"

    @classmethod
    def get_method(cls):
        return "process_upload_attachment_event"

    def __str__(self):
        return self.content
