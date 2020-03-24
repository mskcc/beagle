from django.conf import settings
from notifier.event_handler.event import Event


class RunCompletedEvent(Event):

    def __init__(self, job_group, request_id, run_id, pipeline, run_status, sample_name_tumor, sample_name_normal):
        self.job_group = job_group
        self.request_id = request_id
        self.pipeline = pipeline
        self.run_id = run_id
        self.run_status = run_status
        self.sample_name_tumor = sample_name_tumor
        self.sample_name_normal = sample_name_normal

    @classmethod
    def get_type(cls):
        return "RunCompletedEvent"

    @classmethod
    def get_method(cls):
        return "process_run_completed"

    def __str__(self):
        RUN_TEMPLATE = """

        Run Id: {run_id}
        Pipeline: {pipeline_name}
        Sample Name Tumor: {sample_name_tumor}
        Sample Name Normal: {sample_name_normal}
        Status: {status}
        Link: {link}

        """
        link = "%s%s%s\n" % (settings.BEAGLE_URL, '/v0/run/api/', self.run_id)
        return RUN_TEMPLATE.format(run_id=self.run_id,
                                   pipeline_name=self.pipeline,
                                   sample_name_tumor=self.sample_name_tumor,
                                   sample_name_normal=self.sample_name_normal,
                                   status=self.run_status, link=link)
