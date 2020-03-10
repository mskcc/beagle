import logging
from django.conf import settings
from ..event_handler import EventHandler
from notifier.jira.jira_client import JiraClient
# from notifier.events import *


class JiraEventHandler(EventHandler):
    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.client = JiraClient(settings.JIRA_URL, settings.JIRA_USERNAME, settings.JIRA_PASSWORD, settings.JIRA_PROJECT)

    def process_import_event(self, event):
        self.logger.info("Creating JIRA ticket for requestId: %s and description: %s", event.request_id, str(event))
        self.client.create_ticket(event.request_id, None, str(event))

    def process_operator_run_event(self, event):
        tickets = self.client.get_ticket(event.request_id).json()
        ticket_id = sorted(tickets['issues'], key=lambda i: i['id'], reverse=True)[0]
        self.logger.info(ticket_id, str(event))
        self.client.comment(ticket_id, str(event))

    def run_finished(self, run):
        """
        :return: Update each completed run
        """

    def request_finished(self, request_id, status):
        """
        :return: Request COMPLETED or FAILED (for JIRA this should be change of status and add number of successful/failed runs)
        """
        ticket_id = self.client.get_ticket(request_id).json()['issues'][0]['key']
        transitions = self.client.get_status_transitions(ticket_id)
        transition_id = None
        if transitions.status_code == 200:
            for i in transitions.json()['transitions']:
                if i['name'] == status:
                    transition_id = i['id']
        if transition_id:
            self.client.update_status(request_id, transition_id)

