from django.conf import settings
from notifier.event_handler.event import Event


class OperatorRunEvent(Event):

    def __init__(self, job_group, request_id, pipeline, valid_runs, operator_run_id):
        self.job_group = job_group
        self.request_id = request_id
        self.pipeline = pipeline
        self.valid_runs = valid_runs
        self.operator_run_id = operator_run_id

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
        {tags}
        Link: {link}
        
        """
        comment = """
        OperatorRun {operator_run}
        
        Total runs: {total_runs}
        
        Runs submitted:
        """.format(operator_run=self.operator_run_id, total_runs=len(self.valid_runs))
        for r in self.valid_runs:
            link = "%s%s%s\n" % (settings.BEAGLE_URL, '/v0/run/api/', r['run_id'])
            tags = ""
            for k, v in r['tags'].items():
                tags += "%s: %s\n" % (k, str(v))
            comment += RUN_TEMPLATE.format(run_id=r['run_id'],
                                           pipeline_name=self.pipeline,
                                           tags=tags,
                                           link=link)
        return comment
