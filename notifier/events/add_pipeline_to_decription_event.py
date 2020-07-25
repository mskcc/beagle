from notifier.event_handler.event import Event


class AddPipelineToDescriptionEvent(Event):

    def __init__(self, job_group, pipeline_name, pipeline_version, github_link):
        self.job_group = job_group
        self.pipeline_name = pipeline_name
        self.pipeline_version = pipeline_version
        self.github_link = github_link

    @classmethod
    def get_type(cls):
        return "AddPipelineToDescriptionEvent"

    @classmethod
    def get_method(cls):
        return "process_add_pipeline_to_description_event"

    def __str__(self):
        return '| {pipeline_name} | {pipeline_version} | {pipeline_link} |\n'.format(pipeline_name=self.pipeline_name,
                                                                                     pipeline_version=self.pipeline_version,
                                                                                     pipeline_link=self.github_link)
