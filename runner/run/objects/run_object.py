import logging
from runner.run.objects.port_object import PortObject
from runner.pipeline.pipeline_cache import PipelineCache
from runner.models import PortType, RunStatus, Run, Port
from runner.run.processors.port_processor import PortProcessor, PortAction
from runner.exceptions import PortProcessorException, RunCreateException, RunObjectConstructException


class RunObject(object):
    logger = logging.getLogger(__name__)

    def __init__(self, run_id, run_obj, inputs, outputs, status, job_statuses=None, message={}, output_metadata={},
                 execution_id=None, tags={}, job_group=None, job_group_notifier=None, notify_for_outputs=[]):
        self.run_id = run_id
        self.run_obj = run_obj
        self.output_file_group = run_obj.app.output_file_group
        self.inputs = inputs
        self.outputs = outputs
        self.status = status
        self.job_statuses = job_statuses
        self.message = message
        self.output_metadata = output_metadata
        self.execution_id = execution_id
        self.job_group = job_group
        self.job_group_notifier = job_group_notifier
        self.notify_for_outputs = notify_for_outputs
        self.tags = tags

    @classmethod
    def from_cwl_definition(cls, run_id, inputs):
        """
        :param run_id:
        :param inputs:
        :param output_metadata:
        :param tags:
        :return:
        """
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist:
            raise RunCreateException("Failed to create run. Run with id: %s doesn't exist" % str(run_id))
        try:
            app = PipelineCache.get_pipeline(run.app)
        except Exception as e:
            raise RunCreateException("Failed to create run. Failed to resolve CWL %s" % str(e))
        try:
            input_ports = [PortObject.from_cwl_definition(run_id, inp, PortType.INPUT, inputs) for inp in
                           app.get('inputs', [])]
            output_ports = [PortObject.from_cwl_definition(run_id, out, PortType.OUTPUT, {}) for out in
                            app.get('outputs', [])]
        except PortProcessorException as e:
            raise RunCreateException("Failed to create run: %s" % str(e))
        return cls(run_id,
                   run,
                   input_ports,
                   output_ports,
                   run.status,
                   job_statuses=run.job_statuses,
                   message=run.message,
                   output_metadata=run.output_metadata,
                   tags=run.tags,
                   job_group=run.job_group,
                   job_group_notifier=run.job_group_notifier)

    def ready(self):
        [PortObject.ready(p) for p in self.inputs]
        [PortObject.ready(p) for p in self.outputs]
        self.status = RunStatus.READY

    @classmethod
    def from_db(cls, run_id):
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist:
            raise RunObjectConstructException("Run with id: %s doesn't exist" % str(run_id))
        inputs = [PortObject.from_db(p.id) for p in Port.objects.filter(run_id=run_id, port_type=PortType.INPUT)]
        outputs = [PortObject.from_db(p.id) for p in Port.objects.filter(run_id=run_id, port_type=PortType.OUTPUT)]
        return cls(run_id, run, inputs, outputs, run.status, job_statuses=run.job_statuses, message=run.message,
                   output_metadata=run.output_metadata, tags=run.tags, execution_id=run.execution_id,
                   job_group=run.job_group, job_group_notifier=run.job_group_notifier,
                   notify_for_outputs=run.notify_for_outputs)

    def to_db(self):
        [PortObject.to_db(p) for p in self.inputs]
        [PortObject.to_db(p) for p in self.outputs]
        self.run_obj.status = self.status
        self.run_obj.job_statuses = self.job_statuses
        self.run_obj.message = self.message
        self.run_obj.output_metadata = self.output_metadata
        self.run_obj.execution_id = self.execution_id
        self.run_obj.tags = self.tags
        self.run_obj.job_group = self.job_group
        self.run_obj.job_group_notifier = self.job_group_notifier
        self.run_obj.notify_for_outputs = self.notify_for_outputs
        self.run_obj.save()

    def equal(self, run):
        if self.run_obj.app != run.run_obj.app:
            self.logger.debug("Apps not same")
            self.logger.debug("App 1: %s" % self.run_obj.app)
            self.logger.debug("App 2: %s" % run.run_obj.app)
            return False
        run_1_inputs = set()
        run_2_inputs = set()
        for input1 in self.inputs:
            run_1_inputs.add(input1.name)
        for input2 in run.inputs:
            run_2_inputs.add(input2.name)
        if run_1_inputs != run_2_inputs:
            return False
        for input1 in self.inputs:
            for input2 in run.inputs:
                if input1.name == input2.name:
                    self.logger.debug("Compare input name %s" % input1.name)
                    value1 = PortProcessor.process_files(input1.db_value, PortAction.CONVERT_TO_CWL_FORMAT)
                    value2 = PortProcessor.process_files(input2.db_value, PortAction.CONVERT_TO_CWL_FORMAT)
                    self.logger.debug("Value 1: %s" % value1)
                    self.logger.debug("Value 2: %s" % value2)
                    if value1 != value2:
                        return False
        return True

    def fail(self, error_message):
        self.status = RunStatus.FAILED
        self.message = error_message

    def complete(self, outputs):
        for out in self.outputs:
            out.complete(outputs.get(out.name, None), self.output_file_group, self.job_group_notifier, self.output_metadata)
        self.status = RunStatus.COMPLETED

    def __repr__(self):
        return "(RUN) %s: status: %s" % (self.run_id, RunStatus(self.status).name)
