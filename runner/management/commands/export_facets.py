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
from runner.models import Port


def check_if_operator(related_obj, seen, allowed_operator_pks):
    if related_obj is None:
        return None
    if isinstance(related_obj, OperatorRun):
        if related_obj.operator_id in allowed_operator_pks and related_obj.pk not in seen[type(related_obj)]:
            return related_obj
    else:
        if related_obj.pk not in seen[type(related_obj)]:
            return related_obj
    return None


def collect_related_objects_streaming(starting_objects, allowed_operator_pks, old_prefixes, new_prefix, out_file):
    seen = defaultdict(set)
    queue = deque(starting_objects)
    count = 0
    with open(out_file, "w") as f:
        while queue:
            obj = queue.popleft()
            model = type(obj)

            if obj.pk in seen[model]:
                continue
            seen[model].add(obj.pk)

            # Serialize and immediately write this object
            serialized_obj = json.loads(serialize("json", [obj]))[0]

            edited_obj = edit_serialized_data([serialized_obj], old_prefixes, new_prefix)[0]
            f.write(json.dumps(edited_obj) + "\n")
            f.flush()
            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} objects", flush=True)
            if isinstance(obj, Run):
                for port in obj.port_set.iterator():
                    if port.pk not in seen[Port]:
                        if port.name != "sv_directory":
                            queue.append(port)
                    if hasattr(port, "file") and port.file and port.file.pk not in seen[File]:
                        queue.append(port.file)
            if isinstance(obj, File):
                fg = getattr(obj, "file_group", None)
                if fg and fg.pk not in seen[FileGroup]:
                    queue.append(fg)
            # Handle related objects
            for field in model._meta.get_fields():
                if isinstance(field, (ForeignKey, OneToOneField)):
                    related_obj = getattr(obj, field.name, None)
                    if should_enqueue(related_obj, seen, allowed_operator_pks):
                        queue.append(related_obj)
                elif isinstance(field, ManyToManyField):
                    try:
                        related_manager = getattr(obj, field.name)
                        for related_obj in related_manager.iterator():
                            to_enqueue = check_if_operator(related_obj, seen, allowed_operator_pks)
                            if to_enqueue:
                                queue.append(to_enqueue)
                    except Exception:
                        continue

    print(f"Finished exporting {count} objects to {out_file}", flush=True)


def strip_prefixes(s, prefixes):
    for p in prefixes:
        if s.startswith(p):
            return s[len(p) :]
    return s


def edit_serialized_data(data, old_prefixes, new_prefix):
    for obj in data:
        fields = obj.get("fields", {})
        model_name = obj.get("model", "")

        if model_name.endswith("run"):
            out = fields.get("output_directory")
            if isinstance(out, str):
                fields["output_directory"] = new_prefix + strip_prefixes(out, old_prefixes)

            name = fields.get("name")
            if isinstance(name, str) and not name.startswith("JUNO RUN:"):
                fields["name"] = f"JUNO RUN: {name}"

        if model_name.endswith("pipeline"):
            out = fields.get("output_directory")
            fields["operator"] = fields["operator"] + 100
            if isinstance(out, str):
                fields["output_directory"] = new_prefix + strip_prefixes(out, old_prefixes)

            name = fields.get("name")
            if isinstance(name, str) and not name.startswith("JUNO PIPELINE:"):
                fields["name"] = f"JUNO PIPELINE: {name}"

        if model_name.endswith("operator"):
            slug = fields.get("slug")
            if isinstance(slug, str) and not slug.startswith("JUNO OPERATOR:"):
                fields["slug"] = f"JUNO OPERATOR: {slug}"
                obj["pk"] = obj["pk"] + 100

        if model_name.endswith("operatorrun"):
            slug = fields.get("slug")
            fields["operator"] = fields["operator"] + 100
            fields["parent"] = None

        if model_name.endswith("file"):
            path = fields.get("path")
            fields["path"] = new_prefix + strip_prefixes(path, old_prefixes)

        if model_name.endswith("storage"):
            slug = fields.get("name")
            if slug == "juno":
                fields["name"] = "iris"

        if model_name.endswith("filegroup"):
            fields["slug"] = f"JUNO: {fields['slug']}"
            fields["name"] = f"JUNO: {fields['name']}"

    return data


def serialize_related_objects(seen_dict, old_prefixes, new_prefix):
    data = []
    for model, pks in seen_dict.items():
        queryset = model.objects.filter(pk__in=pks)
        data.extend(json.loads(serialize("json", queryset)))
    edited_data = edit_serialized_data(data, old_prefixes, new_prefix)
    return json.dumps(edited_data, indent=2)


def should_enqueue(related_obj, seen, allowed_operator_pks):
    if related_obj is None:
        return False
    # skip traversing FileGroup → files
    if isinstance(related_obj, FileGroup):
        return False
    if isinstance(related_obj, OperatorRun):
        return related_obj.operator_id in allowed_operator_pks and related_obj.pk not in seen[type(related_obj)]
    return related_obj.pk not in seen[type(related_obj)]


def collect_related_objects_fg(starting_objects):
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
            if isinstance(obj, FileGroup) and field.name == "file_set":
                continue
            if isinstance(field, (ForeignKey, OneToOneField)):
                related_obj = getattr(obj, field.name, None)
                if isinstance(obj, FileGroup) and field.name == "file_set":
                    continue
                if related_obj is None:
                    continue
                else:
                    if related_obj.pk not in seen[type(related_obj)]:
                        queue.append(related_obj)

            if isinstance(obj, File):
                fg = getattr(obj, "file_group", None)
                if fg and fg.name in ("ACCESS SV", "access_curated_normals", "accessv2_curated_normals"):
                    # Only enqueue files if they are already added via a Run/Port
                    pass
            elif isinstance(field, ManyToManyField):
                try:
                    related_manager = getattr(obj, field.name)
                    for related_obj in related_manager.all():
                        if isinstance(obj, FileGroup) and field.name == "file_set":
                            continue
                        if related_obj is None:
                            continue
                        else:
                            if related_obj.pk not in seen[type(related_obj)]:
                                queue.append(related_obj)
                except Exception:
                    continue

    return seen


class Command(BaseCommand):

    help = "Facet exports from JUNO"

    def add_arguments(self, parser):

        # OperatorRuns
        subparsers = parser.add_subparsers(dest="subcommand")

        parser_operator = subparsers.add_parser("operator-run", help="Export an operator and related objects")
        parser_operator.add_argument("--operator", type=str, nargs="+", help="Operator slugs")
        parser_operator.add_argument("--out", type=str, required=True, help="Output JSON file path")
        parser_operator.add_argument(
            "--old-prefixes", type=str, nargs="+", required=True, help="Old path prefixes to strip"
        )
        parser_operator.add_argument("--new-prefix", type=str, required=True, help="New path prefix to add")
        parser_operator.set_defaults(func=self._export_operator)

        # File Groups
        parser_filegroup = subparsers.add_parser("file-group", help="Export an operator and related objects")
        parser_filegroup.add_argument("--filegroups", type=str, nargs="+", help="Filegroup slugs")
        parser_filegroup.add_argument("--out", type=str, required=True, help="Output JSON file path")
        parser_filegroup.add_argument(
            "--old-prefixes", type=str, nargs="+", required=True, help="Old path prefixes to strip"
        )
        parser_filegroup.add_argument("--new-prefix", type=str, required=True, help="New path prefix to add")
        parser_filegroup.set_defaults(func=self._export_filegroup)

    def handle(self, *args, **options):
        func = options.pop("func", None)
        if func:
            return func(options)
        else:
            self.stderr.write("Missing subcommand")

    def _export_operator(self, options):
        operator_args = options["operator"]
        out_prefix = options["out"]  # use as prefix; we'll append operator slug
        old_prefixes = options["old_prefixes"]
        new_prefix = options["new_prefix"]
        total_runs = {}
        allowed_operators = [Operator.objects.get(slug=op) for op in operator_args]
        for op in allowed_operators:
            allowed_operator_pks = {op.pk}

            operator_runs = OperatorRun.objects.filter(
                operator_id=op.pk,
                status=RunStatus.COMPLETED.value,
            )
            # operator_runs = [operator_runs[0]]
            runs = Run.objects.filter(
                operator_run__in=operator_runs,
                status=RunStatus.COMPLETED.value,
            ).iterator()
            out_file = f"{out_prefix}_{op.slug}.json"
            print(f"Starting export for operator {op.slug} → {out_file}", flush=True)

            collect_related_objects_streaming(
                starting_objects=runs,
                allowed_operator_pks=allowed_operator_pks,
                old_prefixes=old_prefixes,
                new_prefix=new_prefix,
                out_file=out_file,
            )

            print(f"Finished export for operator {op.slug}", flush=True)

    def _export_filegroup(self, options):
        filegroup_args = options["filegroups"]
        out_file = options["out"]
        old_prefixes = options["old_prefixes"]
        new_prefix = options["new_prefix"]
        file_groups = [gr for gr in filegroup_args]
        files = File.objects.filter(file_group__slug__in=file_groups)
        related = collect_related_objects_fg(files)
        with open(out_file, "w") as f:
            for model, pks in related.items():
                queryset = model.objects.filter(pk__in=pks).iterator()
                for obj in queryset:
                    serialized_obj = json.loads(serialize("json", [obj]))[0]
                    edited_obj = edit_serialized_data([serialized_obj], old_prefixes, new_prefix)[0]
                    f.write(json.dumps(edited_obj) + "\n")
                    f.flush()


# XSV1
# nohup python3 manage.py export_facets operator-run \
#   --operator AccessLegacySNVOperator AccessLegacySVOperator \
#   --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_ports_v1_test \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/ \
#   > export_facets.log 2>&1 &
# disown

# SV is 13230 runs vs 14552
# python3 manage.py export_facets operator-run \
#   --operator AccessLegacySVOperator \
#   --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_ports_v1_test \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/
# python3 manage.py export_facets operator-run \
#   --operator AccessLegacyOperator AccessLegacySNVOperator AccessLegacySVOperator AccessLegacyCNVOperator AccessLegacyMSIOperator \
#   --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_ports_xsv1_groups \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/

# python3 manage.py export_facets operator-run \
#   --operator AccessLegacyOperator \
#   --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_test_ports.json \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/
# XSV2
# python3 manage.py export_facets operator-run \
#   --operator AccessV2NucleoOperator AccessV2NucleoQcOperator AccessV2NucleoAggQcOperator AccessV2LegacySNVOperator AccessV2LegacyCNVOperator AccessV2LegacySVOperator AccessV2LegacyMSIOperator \
#   --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_ports_xsv2 \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/

# CMO-CH
python3 manage.py export_facets operator-run \
  --operator AccessCMOCHOperator CMOCHQCOperator CMOCHQcAggOperator CMOCHChipVarOperator \
  --out /juno/work/access/production/runs/voyager/facets/export_operatorrun_ports_cmoch_groups \
  --old-prefixes /work/ /juno/work/ \
  --new-prefix /data1/core006/

# python3 manage.py export_facets file-group \
#   --out /juno/work/access/production/runs/voyager/facets/export_filegroup.json \
#   --filegroups accessv2_curated_normals access_curated_normals \
#   --old-prefixes /work/ /juno/work/ \
#   --new-prefix /data1/core006/
