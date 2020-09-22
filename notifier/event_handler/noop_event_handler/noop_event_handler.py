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

    def process_operator_start_event(self, event):
        pass

    def process_etl_jobs_links_event(self, event):
        pass

    def process_etl_set_recipe_event(self, event):
        pass

    def process_operator_run_event(self, event):
        pass

    def process_run_completed(self, event):
        pass

    def process_run_started_event(self, event):
        pass

    def process_operator_request_event(self, event):
        pass

    def process_etl_job_failed_event(self, event):
        pass

    def process_operator_error_event(self, event):
        pass

    def process_assay_event(self, event):
        pass

    def process_custom_capture_cc_event(self, event):
        pass

    def process_redelivery_event(self, event):
        pass

    def process_redelivery_update_event(self, event):
        pass

    def process_set_label_event(self, event):
        pass

    def process_add_pipeline_to_description_event(self, event):
        pass

    def process_set_pipeline_field_event(self, event):
        pass

    def process_transition_event(self, event):
        pass

    def process_upload_attachment_event(self, event):
        pass

    def process_set_run_ticket_in_import_event(self, event):
        pass
