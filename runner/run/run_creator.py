import os
import copy
from runner.models import PortType
from file_system.models import File, FileType, FileRunMap
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

    def __init__(self, run_id, value, type, inputs):
        self.id = value.get('id')
        input_type = value.get('type')
        self.secondary_files = value.get('secondaryFiles', [])
        self.schema = self._resolve_type(input_type)
        self.type = type
        self.value = _resolve_inputs(copy.deepcopy(inputs.get(self.id)))
        self.db_value = _resolve_inputs_db(copy.deepcopy(inputs.get(self.id)), run_id)
        self.run_id = run_id

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


def _resolve_inputs_db(inputs, run_id):
    if inputs and isinstance(inputs, dict):
        new_inputs = dict()
        for k, v in inputs.items():
            if isinstance(v, dict):
                new_inputs[k] = _resolve_inputs_db(v, run_id)
            elif isinstance(v, list):
                new_val = []
                for item in v:
                    new_val.append(_resolve_inputs_db(item, run_id))
                new_inputs[k] = new_val
            else:
                if k == 'location':
                    file_id = _get_file_id(v)
                    new_inputs['location'] = file_id
                    _add_run_to_file(file_id, run_id)
                else:
                    new_inputs[k] = v
        return new_inputs
    return inputs


def _add_run_to_file(file_id, run_id):
    file = FileRunMap.objects.filter(file_id=file_id).first()
    if not file:
        file = FileRunMap(file=File.objects.get(id=file_id), run=[run_id])
    else:
        runs = file.run
        runs.append(run_id)
        file.run = runs
    file.save()


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
        return str(file_obj.id)


def _resolve_outputs(inputs, file_group, metadata):
    if inputs and isinstance(inputs, dict):
        new_inputs = dict()
        for k, v in inputs.items():
            if isinstance(v, dict):
                new_inputs[k] = _resolve_outputs(v, file_group, metadata)
            elif isinstance(v, list):
                new_val = []
                for item in v:
                    new_val.append(_resolve_outputs(item, file_group, metadata))
                new_inputs[k] = new_val
            else:
                if k == 'location':
                    try:
                        path, size = _create_file(v, file_group, metadata)
                    except Exception as e:
                        print(e)
                    else:
                        new_inputs['location'] = path
                        new_inputs['size'] = size
                else:
                    new_inputs[k] = v
        return new_inputs
    elif isinstance(inputs, list):
        new_val = []
        for item in inputs:
            new_val.append(_resolve_outputs(item, file_group, metadata))
        return new_val
    return inputs


def _create_file(filepath, file_group, metadata={}):
    filepath = filepath.replace('file://', '')
    basename = os.path.basename(filepath)
    ext = basename.split('.')[-1]
    try:
        file_type = FileType.objects.get(ext=ext)
    except FileType.DoesNotExist:
        file_type = 'unknown'
    else:
        file_type = file_type.ext
    serializer = CreateFileSerializer(
        data={'path': filepath, 'file_group_id': file_group.id, 'file_type': file_type, 'metadata': metadata})
    if serializer.is_valid():
        file = serializer.save()
        return 'bid://%s' % str(file.id), file.size
    raise Exception('Error when saving file: %s' % serializer.errors)


class Run(object):

    def __init__(self, run_id, app, inputs):
        self.app = app
        self.inputs = [Port(run_id, inp, PortType.INPUT, inputs) for inp in app.get('inputs', [])]
        self.outputs = [Port(run_id, out, PortType.OUTPUT, {}) for out in app.get('outputs', [])]
