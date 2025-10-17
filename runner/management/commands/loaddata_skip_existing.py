# runner/management/commands/loaddata_skip_existing.py

from django.core.management.base import BaseCommand
from django.core.serializers import deserialize
from django.db import transaction, IntegrityError, models
from collections import defaultdict
from django.utils import timezone
import json
import os


class Command(BaseCommand):
    help = "Load NDJSON fixtures but skip existing objects, respecting FK dependencies and logging every action."

    def add_arguments(self, parser):
        parser.add_argument("fixtures", nargs="+", help="Paths to NDJSON fixture files")

    def handle(self, *args, **options):
        fixtures = options["fixtures"]
        all_objects = []
        fixture_pks_by_model = defaultdict(set)

        # load all objects from NDJSON fixture
        for fixture_path in fixtures:
            if not os.path.exists(fixture_path):
                self.stderr.write(self.style.ERROR(f"Fixture not found: {fixture_path}"))
                continue

            self.stdout.write(f"Reading fixture: {fixture_path}")
            with open(fixture_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        for obj in deserialize("json", f"[{line}]"):
                            all_objects.append(obj)
                            fixture_pks_by_model[obj.object.__class__].add(obj.object.pk)
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error parsing line {line_num} of {fixture_path}: {e}"))

        self.stdout.write(f"Total objects loaded: {len(all_objects)}\n")

        # Build dependency order
        dependency_order = self.build_dependency_order(all_objects)
        all_objects.sort(key=lambda o: dependency_order.get(o.object._meta.label_lower, 99))

        # prefetch existing PKs
        existing_pks = {model: set(model.objects.values_list("pk", flat=True)) for model in fixture_pks_by_model}
        inserted_pks = {model: set() for model in fixture_pks_by_model}
        created_or_existing = {}

        deferred = []

        inserted_count = 0
        skipped_count = 0
        while all_objects:
            remaining = []

            for obj in all_objects:
                model = obj.object.__class__
                pk = obj.object.pk

                # Skip if PK exists
                if pk in existing_pks.get(model, set()):
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f"Skipped {model.__name__}({pk}) — already exists (PK)"))
                    created_or_existing[(model._meta.label_lower, pk)] = model.objects.get(pk=pk)
                    continue

                # Skip if unique constraint exists
                if self.exists_by_unique_fields(obj):
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {model.__name__}({pk}) — unique constraint conflict")
                    )
                    unique_filters = self.get_unique_filters(obj)
                    if unique_filters:
                        existing_obj = model.objects.get(**unique_filters)
                        created_or_existing[(model._meta.label_lower, pk)] = existing_obj
                    continue

                # Resolve FKs
                missing_fk = []
                for field in model._meta.fields:
                    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                        fk_id = getattr(obj.object, field.attname)
                        if not fk_id:
                            continue
                        related_model = field.related_model
                        if fk_id in inserted_pks.get(related_model, set()) or fk_id in existing_pks.get(
                            related_model, set()
                        ):
                            rel_instance = related_model.objects.get(pk=fk_id)
                            setattr(obj.object, field.name, rel_instance)
                        else:
                            missing_fk.append(f"{related_model.__name__}({fk_id})")

                # Resolve M2M fields
                m2m_data = {}
                for m2m_field in model._meta.many_to_many:
                    try:
                        rel_pks = [rel.pk for rel in getattr(obj.object, m2m_field.name).all()]
                        m2m_data[m2m_field.name] = rel_pks
                        getattr(obj.object, m2m_field.name).clear()
                    except Exception:
                        continue

                if missing_fk:
                    remaining.append(obj)
                    self.stdout.write(
                        self.style.WARNING(f"Deferring {model.__name__}({pk}) — missing FKs: {', '.join(missing_fk)}")
                    )
                    continue

                # Only auto-fill dates for JobGroup objects
                if model.__name__ == "JobGroup":
                    if not getattr(obj.object, "created_date", None):
                        obj.object.created_date = timezone.now()
                    if not getattr(obj.object, "modified_date", None):
                        obj.object.modified_date = timezone.now()

                # Save **only new objects** — do NOT save if PK already exists
                try:
                    with transaction.atomic():
                        for field_name in ["created_date", "modified_date"]:
                            field = model._meta.get_field(field_name)
                            if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                                auto_now_backup = getattr(field, "auto_now", False)
                                auto_now_add_backup = getattr(field, "auto_now_add", False)
                                field.auto_now = False
                                field.auto_now_add = False

                        obj.object.save()

                        # restore
                        for field_name in ["created_date", "modified_date"]:
                            field = model._meta.get_field(field_name)
                            if field_name == "created_date":
                                field.auto_now_add = auto_now_add_backup
                            else:
                                field.auto_now = auto_now_backup
                        inserted_pks[model].add(pk)
                        created_or_existing[(model._meta.label_lower, pk)] = obj.object
                        inserted_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Inserted {model.__name__}({pk})"))

                    # Assign deferred M2M
                    for field_name, rel_pks in m2m_data.items():
                        if rel_pks:
                            getattr(obj.object, field_name).set(rel_pks)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Assigned M2M for {model.__name__}({pk}) field '{field_name}' -> {rel_pks}"
                                )
                            )

                except IntegrityError as e:
                    remaining.append(obj)
                    self.stderr.write(self.style.ERROR(f"Failed to insert {model.__name__}({pk}): {e}"))

            if len(remaining) == len(all_objects):
                unresolved = [f"{o.object.__class__.__name__}({o.object.pk})" for o in remaining]
                raise IntegrityError(f"Could not resolve dependencies: {', '.join(unresolved)}")

            all_objects = remaining
        self.stdout.write(self.style.SUCCESS(f"\nDone: {inserted_count} inserted, {skipped_count} skipped"))

    def build_dependency_order(self, all_objs):
        """
        Compute a dependency ordering by examining ForeignKey fields.
        Parents come before children.
        """
        graph = {}
        for obj in all_objs:
            model_label = obj.object._meta.label_lower
            deps = set()
            for field in obj.object._meta.fields:
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    deps.add(field.related_model._meta.label_lower)
            graph[model_label] = deps

        # Simple topological sort
        resolved = set()
        order = {}
        for _ in range(20):
            for model_label, deps in graph.items():
                if model_label in order:
                    continue
                if deps.issubset(resolved):
                    order[model_label] = len(resolved)
                    resolved.add(model_label)
        return order

    def exists_by_unique_fields(self, obj):
        """Return True if an object with the same unique fields already exists."""
        model = obj.object.__class__
        qs = model.objects.all()

        # Single-field unique constraints
        filters = {
            f.name: getattr(obj.object, f.attname)
            for f in model._meta.fields
            if f.unique and getattr(obj.object, f.attname) is not None
        }
        if filters and qs.filter(**filters).exists():
            return True

        # Multi-field unique_together constraints
        for unique_fields in model._meta.unique_together:
            ufilters = {f: getattr(obj.object, f) for f in unique_fields if getattr(obj.object, f) is not None}
            if len(ufilters) == len(unique_fields) and qs.filter(**ufilters).exists():
                return True

        return False

    def get_unique_filters(self, obj):
        """Return the dict of fields for unique lookup (single or multi-field)."""
        model = obj.object.__class__
        # single-field unique
        filters = {
            f.name: getattr(obj.object, f.attname)
            for f in model._meta.fields
            if f.unique and getattr(obj.object, f.attname) is not None
        }
        if filters and model.objects.filter(**filters).exists():
            return filters

        # unique_together
        for unique_fields in model._meta.unique_together:
            ufilters = {f: getattr(obj.object, f) for f in unique_fields if getattr(obj.object, f) is not None}
            if len(ufilters) == len(unique_fields) and model.objects.filter(**ufilters).exists():
                return ufilters

        return None
