from django.conf import settings
from notifier.event_handler.event import Event


class ETLJobsLinksEvent(Event):

    def __init__(self, job_group, request_id, etl_jobs):
        self.job_group = job_group
        self.request_id = request_id
        self.etl_jobs = etl_jobs

    @classmethod
    def get_type(cls):
        return "ETLJobsLinksEvent"

    @classmethod
    def get_method(cls):
        return "process_etl_jobs_links_event"

    def __str__(self):
        ETL_COMMENT_MESSAGE_TEMPLATE = """
        ETLJobs:
        | TYPE | LINK | STATUS | MESSAGE |
        {etl_jobs}
        """
        etl_jobs = ""
        for j in self.etl_jobs:
            etl_jobs += "| %s | %s%s%s | %s | %s |\n" % (j[2], settings.BEAGLE_URL, '/v0/etl/jobs/', j[0], j[1], j[3])
        return ETL_COMMENT_MESSAGE_TEMPLATE.format(etl_jobs=etl_jobs)
