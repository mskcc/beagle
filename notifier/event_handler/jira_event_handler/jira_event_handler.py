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

    def process_operator_run_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        # tickets = self.client.search_tickets(event.request_id).json()
        # ticket_id = sorted(tickets['issues'], key=lambda i: i['id'], reverse=True)[0]['key']
        self.client.comment(job_group.jira_id, str(event))

    def process_run_completed(self, event):
        """
        :return: Update each completed run
        """
        tickets = self.client.search_tickets(event.request_id).json()
        for ticket in tickets.get('issues', []):
            comments = self.client.get_comments(ticket['key']).json()
            for comment in comments.get('comments', []):
                if event.run_id in comment['body']:
                    ticket_id = ticket['key']
                    break
        self.client.comment(ticket_id, str(event))

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
