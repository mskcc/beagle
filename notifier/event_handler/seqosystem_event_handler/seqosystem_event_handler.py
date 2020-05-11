from django.conf import settings
from ..event_handler import EventHandler
from notifier.models import JobGroup
from notifier.seqosystem.client import SeqosystemClient
from file_system.models import FileMetadata


class SeqosystemEventHandler(EventHandler):

    def __init__(self):
        super().__init__()
        self.client = SeqosystemClient(settings.SEQOSYSTEM_URL, settings.SEQOSYSTEM_USERNAME, settings.SEQOSYSTEM_PASSWORD, settings.SEQOSYSTEM_PROJECT)

    @property
    def db_name(self):
        return 'seqosystem_id'

    def start(self, request_id):
        pass

    def process_import_event(self, event):
        pass

    def process_etl_jobs_links_event(self, event):
        pass

    def process_etl_set_recipe_event(self, event):
        pass

    def process_etl_job_imported_event(self, event):
        # If so, build workflow chain
        print(event.request_metadata)
        workflows = []
        operator_queue = [Operator.objects.prefetch_related("pipeline_set", "to_triggers__operator").filter(slug="access", active=True)]

        while operator_queue:
            operator = operator_queue.pop()
            workflows = list(operator.pipeline_set.values("pk", "name", "operator_id"))
            for trigger in operator.to_triggers:
                operator_queue.append(trigger.operator)

        self.client.create_job(event.job_group_id, event.sample_id, workflows)

    def process_operator_run_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.seqosystem_id, str(event))

    def process_run_completed(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.seqosystem_id, str(event))

    def process_operator_request_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        self.client.comment(job_group.seqosystem_id, str(event))

    def process_operator_error_event(self, event):
        self._add_comment_event(event)

    def process_transition_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        response = self.client.get_status_transitions(job_group.seqosystem_id)
        for transition in response.json().get('transitions', []):
            if transition.get('name') == str(event):
                self.client.update_status(job_group.seqosystem_id, transition['id'])
                self.logger.debug("Transition to state %s", transition.get('name'))
                break
