from django.conf import settings
from notifier.event_handler.event import Event


class AddAttachmentLinksToDescriptionEvent(Event):
    def __init__(self, job_notifier, request_id, jira_id, file_names):
        self.job_notifier = job_notifier
        self.request_id = request_id
        self.jira_id = jira_id
        self.file_names = file_names

    @classmethod
    def get_type(cls):
        return "AddAttachmentLinksToDescriptionEvent"

    @classmethod
    def get_method(cls):
        return "process_add_attachment_links_to_description_event"

    def __str__(self):
        result = "Delivery Links:\n"
        for file_name in self.file_names:
            url = f"{settings.DELIVERY_FILE_SERVER}/project/{self.request_id}/jira/{self.jira_id}/{file_name}"
            result += f"{url}\n"
        return result
