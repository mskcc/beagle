import logging


class NextflowRunObject(object):
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        run_id,
        run_obj,
        inputs,
        outputs,
        status,
        samples=[],
        job_statuses=None,
        message={},
        output_metadata={},
        execution_id=None,
        tags={},
        job_group=None,
        job_group_notifier=None,
        notify_for_outputs=[],
    ):
        self.run_id = run_id
        self.run_obj = run_obj
        self.output_file_group = run_obj.app.output_file_group
        self.inputs = inputs
        self.outputs = outputs
        self.status = status
        self.samples = samples
        self.job_statuses = job_statuses
        self.message = message
        self.output_metadata = output_metadata
        self.execution_id = execution_id
        self.job_group = job_group
        self.job_group_notifier = job_group_notifier
        self.notify_for_outputs = notify_for_outputs
        self.tags = tags
