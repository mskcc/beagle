from django.conf import settings
from ..event_handler import EventHandler
from notifier.models import JobGroup
from notifier.jira.jira_client import JiraClient


class JiraEventHandler(EventHandler):

    def __init__(self):
        super().__init__()
        self.client = JiraClient(settings.JIRA_URL, settings.JIRA_USERNAME, settings.JIRA_PASSWORD, settings.JIRA_PROJECT)

    @property
    def db_name(self):
        return 'jira_id'

    def start(self, request_id):
        jira_id = JiraClient.parse_ticket_id(
            self.client.create_ticket("{request_id}".format(request_id=request_id), None, "").json())
        self.logger.debug("Starting JIRA Ticket with ID %s" % jira_id)
        return jira_id

    def process_import_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.update_ticket_description(job_group.jira_id, str(event))

    def process_operator_start_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.update_ticket_description(job_group.jira_id, str(event))

    def process_etl_jobs_links_event(self, event):
        self._add_comment_event(event)

    def process_etl_set_recipe_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.update_labels(job_group.jira_id, [str(event)])

    def process_operator_run_event(self, event):
        self._add_comment_event(event)

    def process_run_completed(self, event):
        self._add_comment_event(event)

    def process_operator_request_event(self, event):
        self._add_comment_event(event)

    def process_etl_job_failed_event(self, event):
        self._add_comment_event(event)

    def process_operator_error_event(self, event):
        self._add_comment_event(event)

    def process_assay_event(self, event):
        self._add_comment_event(event)

    def process_custom_capture_cc_event(self, event):
        self._add_comment_event(event)

    def process_redelivery_event(self, event):
        self._set_label(event)

    def process_redelivery_update_event(self, event):
        self._add_comment_event(event)

    def process_set_label_event(self, event):
        self._set_label(event)

    def process_transition_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        response = self.client.get_status_transitions(job_group.jira_id)
        for transition in response.json().get('transitions', []):
            if transition.get('name') == str(event):
                self.client.update_status(job_group.jira_id, transition['id'])
                self._check_transition(job_group.jira_id, str(event), event)
                self.logger.debug("Transition to state %s", transition.get('name'))
                break

    def _check_transition(self, jira_id, expected_status, event):
        response = self.client.get_ticket(jira_id)
        status = response.json()['fields']['status']['name']
        if status == expected_status:
            return
        self.process_transition_event(event)

    def process_upload_attachment_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.add_attachment(job_group.jira_id, event.file_name, event.get_content(), download=event.download)

    def _add_comment_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.jira_id, str(event))

    def _set_label(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        ticket = self.client.get_ticket(job_group.jira_id)
        if ticket.status_code != 200:
            return
        labels = ticket.json()['fields'].get('labels', [])
        labels.append(str(event))
        self.client.update_labels(job_group.jira_id, labels)
