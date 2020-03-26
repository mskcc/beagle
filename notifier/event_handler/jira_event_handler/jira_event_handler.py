from django.conf import settings
from ..event_handler import EventHandler
from notifier.models import JobGroup
from notifier.jira.jira_client import JiraClient


class JiraEventHandler(EventHandler):

    def __init__(self):
        super().__init__()
        self.client = JiraClient(settings.JIRA_URL, settings.JIRA_USERNAME, settings.JIRA_PASSWORD, settings.JIRA_PROJECT)

    def start(self, request_id):
        jira_id = JiraClient.parse_ticket_id(
            self.client.create_ticket("[TEMPLATE] {request_id}".format(request_id=request_id), None, "").json())
        self.logger.debug("Starting JIRA Ticket with ID %s" % jira_id)
        return jira_id

    def process_import_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.update_ticket_summary(job_group.jira_id, event.request_id)
        self.client.update_ticket_description(job_group.jira_id, str(event))

    def process_etl_jobs_links_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.jira_id, str(event))

    def process_etl_set_recipe_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.update_labels(job_group.jira_id, [str(event)])

    def process_operator_run_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.jira_id, str(event))

    def process_run_completed(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.jira_id, str(event))

    def process_operator_error_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.jira_id, str(event))

    def request_finished(self, request_id, status):
        """
        :return: Request COMPLETED or FAILED (for JIRA this should be change of status and add number of successful/failed runs)
        """
        ticket_id = self.client.search_tickets(request_id).json()['issues'][0]['key']
        transitions = self.client.get_status_transitions(ticket_id)
        transition_id = None
        if transitions.status_code == 200:
            for i in transitions.json()['transitions']:
                if i['name'] == status:
                    transition_id = i['id']
        if transition_id:
            self.client.update_status(request_id, transition_id)
