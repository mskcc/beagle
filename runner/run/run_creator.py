import os
import copy
from runner.models import PortType
from file_system.models import File, FileType
from file_system.serializers import CreateFileSerializer


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

    def __init__(self, value, type, inputs):
        self.id = value.get('id')
        input_type = value.get('type')
        self.secondary_files = value.get('secondaryFiles', [])
        self.schema = self._resolve_type(input_type)
        self.type = type
        self.value = _resolve_inputs(copy.deepcopy(inputs.get(self.id)))

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


def _resolve_inputs_db(inputs):
    if inputs and isinstance(inputs, dict):
        new_inputs = dict()
        for k, v in inputs.items():
            if isinstance(v, dict):
                new_inputs[k] = _resolve_inputs(v)
            elif isinstance(v, list):
                new_val = []
                for item in v:
                    new_val.append(_resolve_inputs(item))
                new_inputs[k] = new_val
            else:
                if k == 'location':
                    new_inputs['location'] = _get_file_id(v)
                else:
                    new_inputs[k] = v
        return new_inputs
    return inputs


def _resolve_inputs(inputs):
    if inputs and isinstance(inputs, dict):
        new_inputs = dict()
        for k, v in inputs.items():
            if isinstance(v, dict):
                new_inputs[k] = _resolve_inputs(v)
            elif isinstance(v, list):
                new_val = []
                for item in v:
                    new_val.append(_resolve_inputs(item))
                new_inputs[k] = new_val
            else:
                if k == 'location':
                    path, size = _resolve_uri(v)
                    new_inputs['path'] = path
                    new_inputs['size'] = size
                else:
                    new_inputs[k] = v
        return new_inputs
    elif isinstance(inputs, list):
        new_val = []
        for item in inputs:
            new_val.append(_resolve_inputs(item))
        return new_val
    return inputs


def _resolve_uri(uri):
    if uri.startswith('bid://'):
        beagle_id = uri.replace('bid://', '')
        try:
            file_obj = File.objects.get(id=beagle_id)
        except File.DoesNotExist as e:
            raise Exception("File %s doesn't exist" % uri)
        return file_obj.path
    elif uri.startswith('juno://'):
        juno_path = uri.replace('juno://', '')
        file_obj = File.objects.filter(path=juno_path).first()
        if not file_obj:
            raise Exception("File %s doesn't exist" % uri)
        return file_obj.path, file_obj.size


def _get_file_id(uri):
    if uri.startswith('bid://'):
        beagle_id = uri.replace('bid://', '')
        try:
            file_obj = File.objects.get(id=beagle_id)
        except File.DoesNotExist as e:
            raise Exception("File %s doesn't exist" % uri)
        return file_obj.path
    elif uri.startswith('juno://'):
        juno_path = uri.replace('juno://', '')
        file_obj = File.objects.filter(path=juno_path).first()
        if not file_obj:
            raise Exception("File %s doesn't exist" % uri)
        return file_obj.id


def _resolve_outputs(inputs, file_group):
    if inputs and isinstance(inputs, dict):
        new_inputs = dict()
        for k, v in inputs.items():
            if isinstance(v, dict):
                new_inputs[k] = _resolve_outputs(v, file_group)
            elif isinstance(v, list):
                new_val = []
                for item in v:
                    new_val.append(_resolve_outputs(item, file_group))
                new_inputs[k] = new_val
            else:
                if k == 'location':
                    path, size = _create_file(v, file_group)
                    new_inputs['location'] = path
                    new_inputs['size'] = size
                else:
                    new_inputs[k] = v
        return new_inputs
    elif isinstance(inputs, list):
        new_val = []
        for item in inputs:
            new_val.append(_resolve_outputs(item, file_group))
        return new_val
    return inputs


def _create_file(filepath, file_group):
    filepath = filepath.replace('file://', '')
    basename = os.path.basename(filepath)
    ext = basename.split('.')[-1]
    try:
        file_type = FileType.objects.get(ext=ext)
    except FileType.DoesNotExist:
        file_type = 'unknown'
    serializer = CreateFileSerializer(data={'path': filepath, 'file_group_id': file_group, 'file_type': file_type})
    if serializer.is_valid():
        file = serializer.save()
        return 'bid://%s' % str(file.id), file.size


class Run(object):

    def __init__(self, app, inputs):
        self.app = app
        self.inputs = [Port(inp, PortType.INPUT, inputs) for inp in app.get('inputs', [])]
        self.outputs = [Port(out, PortType.OUTPUT, {}) for out in app.get('outputs', [])]
