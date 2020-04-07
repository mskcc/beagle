from django.conf import settings
from notifier.event_handler.event import Event


class RunCompletedEvent(Event):

    def __init__(self, job_group, request_id, run_id, pipeline, pipeline_link, output_directory, run_status, tags, running, completed, failed, total, operator_run_id):
        self.job_group = job_group
        self.request_id = request_id
        self.pipeline = pipeline
        self.pipeline_link = pipeline_link
        self.output_directory = output_directory
        self.run_id = run_id
        self.run_status = run_status
        self.tags = tags
        self.running = running
        self.completed = completed
        self.failed = failed
        self.total = total
        self.operator_run_id = operator_run_id

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
        Pipeline Link: {pipeline_link}
        Output Directory: {output_directory}
        {tags}
        Status: {status}
        Link: {link}
        
        _____________________________________________
        
        OperatorRun {operator_run} status
        
        Running: {running}
        Completed: {completed}
        Failed: {failed}
        
        TOTAL: {total}

        """
        link = "%s%s%s\n" % (settings.BEAGLE_URL, '/v0/run/api/', self.run_id)
        tags = ""
        for k, v in self.tags.items():
            tags += "%s: %s\n" % (k, str(v))
        return RUN_TEMPLATE.format(run_id=self.run_id,
                                   pipeline_name=self.pipeline,
                                   pipeline_link=self.pipeline_link,
                                   status=self.run_status,
                                   link=link,
                                   running=str(self.running),
                                   completed=str(self.completed),
                                   failed=str(self.failed),
                                   total=str(self.total),
                                   tags=tags,
                                   operator_run=self.operator_run_id
                                   )
