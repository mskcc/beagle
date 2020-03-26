from ..event_handler import EventHandler


class NoOpEventHandler(EventHandler):

    def __init__(self):
        super().__init__()

    def start(self, request_id):
        pass

    def process_import_event(self, event):
        pass

    def process_etl_jobs_links_event(self, event):
        pass

    def process_etl_set_recipe_event(self, event):
        pass

    def process_operator_run_event(self, event):
        pass

    def process_run_completed(self, event):
        pass

    def request_finished(self, request_id, status):
        pass
