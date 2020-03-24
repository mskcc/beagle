from django.conf import settings
from notifier.event_handler.event import Event


class OperatorRunEvent(Event):

    def __init__(self, job_group, request_id, pipeline, valid_runs):
        self.job_group = job_group
        self.request_id = request_id
        self.pipeline = pipeline
        self.valid_runs = valid_runs

    @classmethod
    def get_type(cls):
        return "OperatorRunEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_run_event"

    def __str__(self):
        RUN_TEMPLATE = """
        
        Run Id: {run_id}
        Pipeline: {pipeline_name}
        Sample Name Tumor: {sample_name_tumor}
        Sample Name Normal: {sample_name_normal}
        Link: {link}
        
        """
        comment = "Runs submitted:\n"
        for r in self.valid_runs:
            link = "%s%s%s\n" % (settings.BEAGLE_URL, '/v0/run/api/', r['run_id'])
            comment += RUN_TEMPLATE.format(run_id=r['run_id'],
                                           pipeline_name=self.pipeline,
                                           sample_name_tumor=r['sample_name_tumor'],
                                           sample_name_normal=r['sample_name_normal'],
                                           link=link)
        return comment
