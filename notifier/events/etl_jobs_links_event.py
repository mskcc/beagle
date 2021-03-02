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

    def translate_status(self, status, message):
        if message:
            try:
                code = message.get('code')
                if code == 101:
                    return "DATA_SOURCE_ERROR"
                elif code == 102:
                    return "NO_DATA"
                elif code == 103:
                    return "ERROR"
            except Exception as e:
                print(e)
        return status

    def get_message(self, message):
        try:
            return message.get('message')
        except Exception as e:
            pass
        return message

    def __str__(self):
        ETL_COMMENT_MESSAGE_TEMPLATE = """
        ETLJobs:
        | TYPE | SAMPLE ID | LINK | STATUS | MESSAGE |
        {etl_jobs}
        """
        etl_jobs = ""
        for j in self.etl_jobs:
            etl_jobs += "| %s | %s | %s%s%s | %s | %s |\n" % (
            j[2], j[4], settings.BEAGLE_URL, '/v0/etl/jobs/', j[0], self.translate_status(j[1], j[3]), self.get_message(j[3]))
        return ETL_COMMENT_MESSAGE_TEMPLATE.format(etl_jobs=etl_jobs)
