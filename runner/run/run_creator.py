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
        self.secondary_files = value.get('secondaryFiles', [])
        self.schema = self._resolve_type(input_type)
        self.type = type
        self.value = None

    def _resolve_type(self, input_type, required=True):
        if isinstance(input_type, dict):
            port_type = input_type.get('type')
            if port_type == 'record':
                t = {
                    'type': 'record',
                    'fields': {}
                }
                for k, v in input_type.get('fields').items():
                    t['fields'][k] = self._resolve_type(v)
                return t if required else ['null', t]
            elif port_type == 'array':
                t = {
                    'type': 'array',
                    'items': self._resolve_type(input_type.get('items')).get('type')
                }
                return t if required else ['null', t]

        elif isinstance(input_type, list):
            resolved_types = []
            required = True
            if "null" in input_type:
                required = False
                input_type.remove("null")
            for pt in input_type:
                resolved_types.append(self._resolve_type(pt))
            if required:
                resolved_types = ['null'].extend(resolved_types)
                return resolved_types
            else:
                return resolved_types[0] if len(resolved_types) == 1 else resolved_types

        elif isinstance(input_type, str):
            is_required = True
            simple_type = input_type
            is_array = True
            if simple_type.endswith('?'):
                simple_type = simple_type.replace('?', '')
                t = {
                    'type': simple_type
                }
                is_required = False
            if simple_type.endswith('[]'):
                simple_type = input_type
                simple_type = simple_type.replace('[]', '')
                is_array = True

            if is_array:
                ttype = 'array'
                items = simple_type
                if is_required:
                    ttype = ['null', 'array']
                t = {
                    'type': ttype,
                    'items': items
                }
            else:
                if is_required:
                    t = {'type': simple_type}
                else:
                    t = {'type': ['null', simple_type]}
            return t


class Run(object):

    def __init__(self, app):
        self.app = app
        self.inputs = [Port(inp, PortType.INPUT) for inp in app.get('inputs', [])]
        self.outputs = [Port(out, PortType.OUTPUT) for out in app.get('outputs', [])]
