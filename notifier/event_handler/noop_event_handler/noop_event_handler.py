from ..event_handler import EventHandler


class NoOpEventHandler(EventHandler):

    def __init__(self):
        super().__init__()

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

    def process_operator_request_event(self, event):
        pass

    def process_etl_job_failed_event{self, event):
        pass

    def process_operator_run_event(self, event):
        pass

    def process_set_label_event(self, event):
        pass

    def process_run_completed(self, event):
        pass

    def process_operator_error_event(self, event):
        pass

    def process_transition_event(self, event):
        pass

    def process_upload_attachment_event(self, event):
        pass
