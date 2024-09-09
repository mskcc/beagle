from notifier.event_handler.event import Event


class LocalStoreAttachmentsEvent(Event):
    def __init__(self, job_notifier, file_name, content):
        self.job_notifier = job_notifier
        self.file_name = file_name
        self.content = content

    @classmethod
    def get_type(cls):
        return "LocalStoreAttachmentsEvent"

    @classmethod
    def get_method(cls):
        return "process_local_store_attachments"

    def __str__(self):
        return self.content
