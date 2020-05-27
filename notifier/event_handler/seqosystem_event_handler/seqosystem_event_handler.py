from django.conf import settings
from ..event_handler import EventHandler
from notifier.models import JobGroup
from notifier.seqosystem.client import SeqosystemClient
from file_system.models import FileMetadata
from beagle_etl.models import Operator


class SeqosystemEventHandler(EventHandler):

    def __init__(self):
        super().__init__()
        self.client = SeqosystemClient(settings.SEQOSYSTEM_URL)

    @property
    def db_name(self):
        return None

    def start(self, request_id):
        pass

    def process_import_event(self, event):
        pass

    def process_etl_jobs_links_event(self, event):
        pass

    def process_etl_set_recipe_event(self, event):
        pass

    def _build_workflow_tree(self, operators):
        workflows = []
        for operator in operators:
            for w in operator.pipeline_set.all():
                workflows.append({
                    "name": w.name,
                    "children": self._build_workflow_tree([t.to_operator for t in operator.from_triggers.all()])
                })
        return workflows

    def process_etl_job_created_event(self, event):
        if event.request_metadata["recipe"] != "MSK-ACCESS_v1":
            return

        workflows = {
            "name": "Beagle Initiated",
            "status": "success",
            "children": self._build_workflow_tree(
                Operator.objects.prefetch_related("pipeline_set", "from_triggers__to_operator").filter(slug="access", active=True).all()
            )
        }

        self.client.create_job(event.job_group_id, event.sample_id, workflows)

    def process_operator_run_event(self, event):
        pass

    def process_run_completed(self, event):
        self.client.complete_job(event.job_group_id, event.pipeline.name, event.tags.sample_id)

    def process_run_failed(self, event):
        self.client.fail_job(event.job_group_id, event.pipeline.name, event.tags.sample_id)

    def process_run_started(self, event):
        self.client.start_job(event.job_group_id, event.pipeline.name, event.tags.sample_id)

    def process_operator_request_event(self, event):
        pass

    def process_operator_error_event(self, event):
        pass

    def process_transition_event(self, event):
        job_group = JobGroup.objects.get(id=event.job_group)
        response = self.client.get_status_transitions(job_group.seqosystem_id)
        for transition in response.json().get('transitions', []):
            if transition.get('name') == str(event):
                self.client.update_status(job_group.seqosystem_id, transition['id'])
                self.logger.debug("Transition to state %s", transition.get('name'))
                break
