from notifier.event_handler.event import Event


class ChronosMissingSamplesEvent(Event):
    def __init__(self, job_notifier, samples):
        self.job_notifier = job_notifier
        self.samples = samples

    @classmethod
    def get_type(cls):
        return "ChronosMissingSamplesEvent"

    @classmethod
    def get_method(cls):
        return "process_chronos_missing_samples_event"

    def __str__(self):
        CHRONOS_MISSING_SAMPLES = """
        Samples not found:
        {samples}
        """
        return CHRONOS_MISSING_SAMPLES.format(
            error=self.samples,
        )
