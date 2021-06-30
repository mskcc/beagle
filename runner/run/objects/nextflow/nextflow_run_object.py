import os
import logging
from runner.run.objects.run_object import RunObject
from runner.pipeline.pipeline_cache import PipelineCache
from runner.run.processors.file_processor import FileProcessor
from runner.models import Run, RunStatus, Port, PortType, ProtocolType
from runner.run.objects.nextflow.nextflow_port_object import NextflowPortObject
from runner.exceptions import PortProcessorException, RunCreateException, RunObjectConstructException


class NextflowRunObject(RunObject):
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
        config=None
    ):
        self.config=config
        self.run_type = ProtocolType.NEXTFLOW
        super().__init__(run_id, run_obj, inputs, outputs, status, samples, job_statuses, message, output_metadata,
                         execution_id, tags, job_group, job_group_notifier, notify_for_outputs)

    @classmethod
    def from_definition(cls, run_id, inputs):
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
            input_ports = [NextflowPortObject.from_definition(run_id, inp, PortType.INPUT, inputs) for inp in
                           app.get('inputs', [])]
            output_ports = [NextflowPortObject.from_definition(run_id, out, PortType.OUTPUT, {}) for out in
                            app.get('outputs', [])]
        except PortProcessorException as e:
            raise RunCreateException("Failed to create run: %s" % str(e))
        return cls(run_id,
                   run,
                   input_ports,
                   output_ports,
                   run.status,
                   samples=[],
                   job_statuses=run.job_statuses,
                   message=run.message,
                   output_metadata=run.output_metadata,
                   tags=run.tags,
                   job_group=run.job_group,
                   job_group_notifier=run.job_group_notifier,
                   config=run.app.config)

    def ready(self):
        [NextflowPortObject.ready(p) for p in self.inputs]
        samples = set()
        for p in self.inputs:
            for f in p.files:
                file_obj = FileProcessor.get_file_obj(f)
                if file_obj.sample:
                    samples.add(file_obj.sample)
        self.samples = list(samples)
        [NextflowPortObject.ready(p) for p in self.outputs]
        self.status = RunStatus.READY

    @classmethod
    def from_db(cls, run_id):
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist:
            raise RunObjectConstructException("Run with id: %s doesn't exist" % str(run_id))
        inputs = [NextflowPortObject.from_db(p.id) for p in
                  Port.objects.filter(run_id=run_id, port_type=PortType.INPUT)]
        outputs = [NextflowPortObject.from_db(p.id) for p in
                   Port.objects.filter(run_id=run_id, port_type=PortType.OUTPUT)]
        return cls(run_id, run, inputs, outputs, run.status, job_statuses=run.job_statuses, message=run.message,
                   output_metadata=run.output_metadata, tags=run.tags, execution_id=run.execution_id,
                   job_group=run.job_group, job_group_notifier=run.job_group_notifier,
                   notify_for_outputs=run.notify_for_outputs, samples=list(run.samples.all()), config=run.app.config)

    def to_db(self):
        [NextflowPortObject.to_db(p) for p in self.inputs]
        [NextflowPortObject.to_db(p) for p in self.outputs]
        self.run_obj.status = self.status
        self.run_obj.samples.set(self.samples)
        self.run_obj.job_statuses = self.job_statuses
        self.run_obj.message = self.message
        self.run_obj.output_metadata = self.output_metadata
        self.run_obj.execution_id = self.execution_id
        self.run_obj.tags = self.tags
        self.run_obj.job_group = self.job_group
        self.run_obj.job_group_notifier = self.job_group_notifier
        self.run_obj.notify_for_outputs = self.notify_for_outputs
        self.run_obj.config = self.config
        self.run_obj.save()

    def complete(self, outputs):
        for out in self.outputs:
            out.complete(outputs.get(out.name, None),
                         self.output_file_group,
                         self.job_group_notifier,
                         self.output_metadata)
        self.status = RunStatus.COMPLETED

    def dump_job(self, output_directory=None):
        app = {
            "github": {
                "repository": self.run_obj.app.github,
                "entrypoint": self.run_obj.app.entrypoint,
                "version": self.run_obj.app.version
            }
        }
        inputs = dict()
        input_files = list()
        params = dict()
        for port in self.inputs:
            if port.template:
                input_files.append({'name': port.name, 'content': port.value})
            else:
                params[port.name] = port.value
        inputs['inputs'] = input_files
        inputs['config'] = self.run_obj.app.config.replace('\\r\\n', '\r\n').replace('\\"', '\"')
        inputs['profile'] = 'juno'
        inputs['params'] = params
        if not output_directory:
            output_directory = os.path.join(self.run_obj.app.output_directory, str(self.run_id))
        job = {
            'type': self.run_type.value,
            'app': app,
            'inputs': inputs,
            'root_dir': output_directory,
        }
        return job

    def __repr__(self):
        return "(RUN) %s: status: %s" % (self.run_id, RunStatus(self.status).name)
