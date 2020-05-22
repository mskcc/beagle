from notifier.event_handler.event import Event


class DisabledAssayEvent(Event):

    def __init__(self, job_group, assay):
        self.job_group = job_group
        self.assay = assay

    @classmethod
    def get_type(cls):
        return "DisabledAssayEvent"

    @classmethod
    def get_method(cls):
        return "process_assay_event"

    def __str__(self):
        TEMPLATE = """
        Assay: {assay} currently not run by CI.
        """
        return TEMPLATE.format(assay=self.assay)
