import ast
from django.conf import settings
from notifier.event_handler.event import Event


class ETLJobsLinksEvent(Event):
    def __init__(self, job_notifier, request_id, etl_jobs):
        self.job_notifier = job_notifier
        self.request_id = request_id
        self.etl_jobs = etl_jobs

    @classmethod
    def get_type(cls):
        return "ETLJobsLinksEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_jobs_links_event"

    def translate_status(self, code=None, message=""):
        if code:
            if code == 101:
                return "DATA_SOURCE_ERROR"
            elif code == 102:
                return "NO_DATA"
            elif code == 103:
                return "ERROR"
        return message

    def get_message(self, message):
        try:
            return message.get("message")
        except Exception as e:
            pass
        return message

    def __str__(self):
        ETL_COMMENT_MESSAGE_TEMPLATE = """
        ETLJobs:
        | TYPE | SAMPLE ID | STATUS | MESSAGE |
        {etl_jobs}
        """
        etl_jobs = ""
        for j in self.etl_jobs:
            etl_jobs += "| %s | %s | %s | %s |\n" % (
                j["type"],
                j["sample"],
                self.translate_status(code=j["code"], message=j["status"]),
                j["message"],
            )
        return ETL_COMMENT_MESSAGE_TEMPLATE.format(etl_jobs=etl_jobs)
