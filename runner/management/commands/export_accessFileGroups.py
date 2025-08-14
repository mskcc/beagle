from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
from django.core.serializers import serialize
from collections import defaultdict
import json
from django.db.models import Max, Q
from file_system.models import File, FileGroup, Sample, Request
from beagle_etl.models import Operator, JobGroup, JobGroupNotifier, Job, JobStatus, ETLConfiguration
from runner.models import OperatorRun, RunStatus, TriggerRunType, Run, Pipeline
from file_system.repository.file_repository import FileRepository
from collections import defaultdict, deque
ACCESS_FACTS="/juno/work/access/production/runs/voyager/facets/"

def collect_related_objects(starting_objects):
    seen = defaultdict(set)
    queue = deque(starting_objects)
    while queue:
        obj = queue.popleft()
        print(obj)
        model = type(obj)

        if obj.pk in seen[model]:
            continue

        seen[model].add(obj.pk)

        for field in model._meta.get_fields():
            if isinstance(field, (ForeignKey, OneToOneField)):
                related_obj = getattr(obj, field.name, None)
                if related_obj is None:
                    continue
                else:
                    if related_obj.pk not in seen[type(related_obj)]:
                        queue.append(related_obj)
            elif isinstance(field, ManyToManyField):
                try:
                    related_manager = getattr(obj, field.name)
                    for related_obj in related_manager.all():
                        if related_obj is None:
                            continue
                        else:
                            if related_obj.pk not in seen[type(related_obj)]:
                                queue.append(related_obj)
                except Exception:
                    continue

    return seen

def edit_serialized_data(data):
    OLD_PREFIX = "/work/"
    NEW_PREFIX = "/data1/core006/"

    for obj in data:
        fields = obj.get("fields", {})
        model_name = obj.get("model", "")
        path = fields.get("path")
        if model_name.endswith("file"):
            if isinstance(path, str) and OLD_PREFIX in path:
                fields["path"] = path.replace(OLD_PREFIX, NEW_PREFIX)
                path = fields.get("path")
    return data

def serialize_related_objects(seen_dict):
    data = []
    for model, pks in seen_dict.items():
        queryset = model.objects.filter(pk__in=pks)
        data.extend(json.loads(serialize('json', queryset)))
    edited_data = edit_serialized_data(data)
    return json.dumps(edited_data, indent=2)

file_groups= ["accessv2_curated_normals", "access_curated_normals"]
files = File.objects.filter(file_group__slug__in=file_groups)
related = collect_related_objects(files)
json_output = serialize_related_objects(related)

with open(ACCESS_FACTS + "curated_file_group.json", "w") as f:
    f.write(json_output)