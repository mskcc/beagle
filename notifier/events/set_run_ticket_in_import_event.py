from django.conf import settings
from notifier.event_handler.event import Event


class SetRunTicketInImportEvent(Event):

    def __init__(self, job_group, run_jira_id):
        self.job_group = job_group
        self.run_jira_id = run_jira_id

    @classmethod
    def get_type(cls):
        return "SetRunTicketInImportEvent"

    @classmethod
    def get_method(cls):
        return "process_set_run_ticket_in_import_event"

    def __str__(self):
        if not self.run_jira_id:
            comment = "Could not find Import JIRA ticket"
        else:
            comment = "Run JIRA Id: {jira_url}/browse/{jira_id}".format(jira_url=settings.JIRA_URL,
                                                                        jira_id=self.run_jira_id)
        return comment
