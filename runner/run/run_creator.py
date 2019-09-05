from runner.models import PortType


class Port(object):

    CWLTypes = ['Any',
                'null',
                'boolean',
                'int',
                'long',
                'float',
                'double',
                'string',
                'File',
                'Directory',
                'array',
                'record']

    def __init__(self, value, type):
        self.id = value.get('id')
        input_type = value.get('type')
        secondary_files = value.get('secondaryFiles', [])
        self.schema = self._schema_evaluate(input_type, secondary_files)
        self.type = type
        self.value = None

    def _schema_evaluate(self, input_type, secondary_files):
        if isinstance(input_type, dict):
            t = input_type.get('type')
            if t not in self.CWLTypes:
                raise Exception("Invalid Port Type")
        elif input_type.endswith('[]'):
            simple_type = input_type
            simple_type = simple_type.replace('[]', '')
            t = {
                'type': 'array',
                'items': simple_type
            }
        else:
            t = input_type
        return {
            "type": t,
            "secondaryFiles": secondary_files
        }


class Run(object):

    def __init__(self, app):
        self.app = app
        self.inputs = [Port(inp, PortType.INPUT) for inp in app.get('inputs', [])]
        self.outputs = [Port(out, PortType.OUTPUT) for out in app.get('outputs', [])]
