import logging
from runner.run.processors.file_processor import FileProcessor
from runner.run.objects.cwl.cwl_port_object import CWLPortObject
from runner.models import RunStatus


class RunObject(object):
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

    @classmethod
    def from_definition(cls, run_id, inputs):
        """
        :param run_id:
        :param inputs:
        :param output_metadata:
        :param tags:
        :return: RunObject
        """

    def ready(self):
        """
        Prepare Run for submit
        :return:
        """

        [CWLPortObject.ready(p) for p in self.inputs]
        samples = set()
        for p in self.inputs:
            for f in p.files:
                file_obj = FileProcessor.get_file_obj(f)
                if file_obj.sample:
                    samples.add(file_obj.sample)
        self.samples = list(samples)
        [CWLPortObject.ready(p) for p in self.outputs]
        self.status = RunStatus.READY

    @classmethod
    def from_db(cls, run_id):
        """
        :param run_id:
        :return: RunObject
        """

    def to_db(self):
        """
        :return:
        """

    def equal(self, run):
        """
        Compare current run to another run
        :param run:
        :return: Boolean
        """

    def fail(self, error_message):
        self.status = RunStatus.FAILED
        self.message = error_message

    def complete(self, outputs):
        pass

    def dump_job(self, output_directory=None):
        """
        :return: Job Dict
        """
        pass
