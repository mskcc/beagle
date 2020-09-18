from django.conf import settings
from notifier.event_handler.event import Event


class RunStartedEvent(Event):

    def __init__(self, job_notifier, run_id, pipeline, pipeline_link, output_directory, tags):
        self.job_notifier = job_notifier
        self.pipeline = pipeline
        self.pipeline_link = pipeline_link
        self.output_directory = output_directory
        self.run_id = run_id
        self.tags = tags

    @classmethod
    def get_type(cls):
        return "RunStartedEvent"

    @classmethod
    def get_method(cls):
        return "process_run_started_event"

    def __str__(self):
        RUN_TEMPLATE = """

        Run Id: {run_id}
        Pipeline: {pipeline_name}
        Pipeline Link: {pipeline_link}
        Output Directory: {output_directory}
        {tags}
        Link: {link}

        """
        link = "%s%s%s\n" % (settings.BEAGLE_URL, '/v0/run/api/', self.run_id)
        tags = ""
        for k, v in self.tags.items():
            tags += "%s: %s\n" % (k, str(v))
        return RUN_TEMPLATE.format(run_id=self.run_id,
                                   pipeline_name=self.pipeline,
                                   pipeline_link=self.pipeline_link,
                                   link=link,
                                   tags=tags,
                                   output_directory=self.output_directory
                                   )
