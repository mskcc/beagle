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
from django.core.management.base import BaseCommand


def check_if_operator(related_obj, seen, allowed_operator_pks):
    if related_obj is None:
        return None
    if isinstance(related_obj, OperatorRun):
        # Only keep OperatorRuns whose operator is allowed
        if related_obj.operator_id in allowed_operator_pks and related_obj.pk not in seen[type(related_obj)]:
            return related_obj
    else:
        if related_obj.pk not in seen[type(related_obj)]:
            return related_obj
    
    return None

def collect_related_objects(starting_objects, allowed_operators_pks):
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
                to_enqueue = check_if_operator(related_obj, seen, allowed_operators_pks)
                if to_enqueue:
                    queue.append(to_enqueue)

            elif isinstance(field, ManyToManyField):
                try:
                    related_manager = getattr(obj, field.name)
                    for related_obj in related_manager.all():
                        to_enqueue = check_if_operator(related_obj, seen, allowed_operators_pks)
                        if to_enqueue:
                            queue.append(to_enqueue)
                except Exception:
                    continue

    return seen


def strip_prefixes(s, prefixes):
    for p in prefixes:
        if s.startswith(p):
            s = s.lstrip(p)
    return s

def edit_serialized_data(data, old_prefix, new_prefix):
    for obj in data:
        fields = obj.get("fields", {})
        model_name = obj.get("model", "")
        # Fix output_directory path
        if model_name.endswith("run"):
            out = fields.get("output_directory")
            if isinstance(out, str):
                fields["output_directory"] = new_prefix + strip_prefixes(out, old_prefix)

            name = fields.get("name")
            if isinstance(name, str) and not name.startswith("JUNO RUN:"):
                fields["name"] = f"JUNO RUN: {name}"

        if model_name.endswith("pipeline"):
            out = fields.get("output_directory")
            if isinstance(out, str):
                fields["output_directory"] = new_prefix + strip_prefixes(out, old_prefix)

            name = fields.get("name")
            if isinstance(name, str) and not name.startswith("JUNO PIPELINE:"):
                fields["name"] = f"JUNO PIPELINE: {name}"

        if model_name.endswith("operator"):
            slug = fields.get("slug")
            if isinstance(slug, str) and not slug.startswith("JUNO OPERATOR:"):
                fields["slug"] = f"JUNO OPERATOR: {slug}"
        if data is None:
            print("Data is None, cannot edit serialized data")
    return data

def serialize_related_objects(seen_dict):
    data = []
    for model, pks in seen_dict.items():
        queryset = model.objects.filter(pk__in=pks)
        data.extend(json.loads(serialize('json', queryset)))
    edited_data = edit_serialized_data(data, ["/work/"], "/data1/core006/")
    return json.dumps(edited_data, indent=2)

class Command(BaseCommand):

    help = "Facet export for OperatorRuns"

    def add_arguments(self, parser):
        parser.add_argument("--operator", type=str, nargs="+", help="Operator slugs")
        parser.add_argument("--out", type=str, required=True)

    def handle(self, *args, **options):
        operator_args = args["operator"]
        out = args["out-dir"]
        operator_args = ["AccessLegacyOperator"]
        allowed_operators = []
        for op in operator_args:
            allowed_operators.append(Operator.objects.get(slug=op))
        allowed_operator_pks = {op.pk for op in allowed_operators}

        operator_runs = OperatorRun.objects.filter(operator_id__in=allowed_operator_pks, status=RunStatus.COMPLETED.value)
        operator_run_ids = operator_runs.values_list('id',flat=True)
        
        # operator_run_ids_shrt = ["12d9314e-facb-11ef-b48b-ac1f6bb4ad16"]
        runs = Run.objects.filter(operator_run__in=operator_run_ids, status=RunStatus.COMPLETED.value)
        latest_by_request = (
            runs
            .values('tags__igoRequestId')
            .annotate(latest_date=Max('finished_date'))
        )

        id_and_date = [(row['tags__igoRequestId'], row['latest_date']) for row in latest_by_request]

        # Step 3: Filter runs that match those (igoRequestId, finished_date) pairs
        query = Q()
        for igo_id, date in id_and_date:
            query |= Q(tags__igoRequestId=igo_id, finished_date=date)

        recent_requests = runs.filter(query)

        related = collect_related_objects(recent_requests, allowed_operator_pks)
        json_output = serialize_related_objects(related)
        # out = "/juno/work/access/production/runs/voyager/facets/"
        with open(out_dir + "xs_legacy_operator_facet_export_2.json", "w") as f:
            f.write(json_output)
