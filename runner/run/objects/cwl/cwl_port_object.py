import copy
from runner.models import Port, PortType, Run
from runner.exceptions import PortObjectConstructException
from runner.run.objects.cwl.processors.file_processor import FileProcessor
from runner.run.objects.cwl.processors.schema_processor import SchemaProcessor
from runner.run.objects.cwl.processors.port_processor import PortProcessor, PortAction


class CWLPortObject(object):

    def __init__(self,
                 run_id,
                 name,
                 port_type,
                 schema,
                 secondary_files,
                 db_value,
                 value,
                 files,
                 port_id=None,
                 notify=False):
        self.run_id = run_id
        self.name = name
        self.port_type = port_type
        self.schema = schema
        self.secondary_files = secondary_files
        self.db_value = db_value
        self.value = value
        self.files = files
        self.port_id = port_id
        self.port_object = None
        self.notify = notify
        if port_id:
            try:
                self.port_object = Port.objects.get(id=port_id)
            except Port.DoesNotExist:
                pass

    @classmethod
    def from_cwl_definition(cls, run_id, value, port_type, port_values, notify=False):
        name = value.get('id')
        input_schema = value.get('type')
        secondary_files = value.get('secondaryFiles', [])
        schema = input_schema
        port_type = port_type
        value = copy.deepcopy(port_values.get(name))
        files = []
        db_value = copy.deepcopy(port_values.get(name))
        notify = notify
        return cls(run_id, name, port_type, schema, secondary_files, db_value, value, files, notify)

    def ready(self):
        self.schema = SchemaProcessor.resolve_cwl_type(self.schema)
        files = []
        self.db_value = PortProcessor.process_files(copy.deepcopy(self.value),
                                                    PortAction.CONVERT_TO_BID,
                                                    file_list=files)
        self.value = PortProcessor.process_files(copy.deepcopy(self.value),
                                                 PortAction.CONVERT_TO_PATH)
        self.files = files

    def complete(self, value, group, job_group_notifier, output_metadata={}):

        self.value = value
        files = []
        self.db_value = PortProcessor.process_files(copy.deepcopy(self.value),
                                                    PortAction.REGISTER_OUTPUT_FILES,
                                                    file_list=files,
                                                    group_id=str(group.id),
                                                    metadata=output_metadata)
        if self.notify:
            PortProcessor.process_files(copy.deepcopy(self.value),
                                        PortAction.SEND_AS_NOTIFICATION,
                                        job_group=job_group_notifier,
                                        download=True)
        self.files = files

    @classmethod
    def from_db(cls, port_id):
        try:
            port = Port.objects.get(id=port_id)
        except Port.DoesNotExist:
            raise PortObjectConstructException('Port with id:')
        return cls(str(port.run.id),
                   port.name,
                   port.port_type,
                   port.schema,
                   port.secondary_files,
                   port.db_value,
                   port.value,
                   [FileProcessor.get_bid_from_file(f) for f in port.files.all()],
                   port_id=port_id,
                   notify=port.notify)

    def to_db(self):
        if self.port_object:
            self.port_object.name = self.name
            self.port_object.port_type = self.port_type
            self.port_object.schema = self.schema
            self.port_object.secondary_files = self.secondary_files
            self.port_object.db_value = self.db_value
            self.port_object.value = self.value
            self.port_object.save()
            self.port_object.files.set([FileProcessor.get_file_obj(v) for v in self.files])
            self.port_object.notify = self.notify
            self.port_object.save()
        else:
            try:
                run_object = Run.objects.get(id=self.run_id)
            except Run.DoesNotExist:
                raise PortObjectConstructException("Port save failed. Run with id: %s doesn't exist.")
            new_port = Port(run=run_object,
                            name=self.name,
                            port_type=self.port_type,
                            schema=self.schema,
                            secondary_files=self.secondary_files,
                            db_value=self.db_value,
                            value=self.value,
                            notify=self.name in run_object.notify_for_outputs
                            )
            new_port.save()
            new_port.files.set([FileProcessor.get_file_obj(v) for v in self.files])
            new_port.save()
            self.port_object = new_port

    def __repr__(self):
        return "(PORT) %s: Name: %s Type: %s" % (self.port_object.id, self.name, PortType(self.port_type).name)
