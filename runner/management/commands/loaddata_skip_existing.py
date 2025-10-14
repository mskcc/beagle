# runner/management/commands/loaddata_skip_existing.py

from django.core.management.base import BaseCommand
from django.core.serializers import deserialize
from django.db import transaction, IntegrityError
from collections import defaultdict
import json

class Command(BaseCommand):
    help = (
        "Load NDJSON fixtures but skip objects that already exist. "
        "Handles PK and unique constraints, FK and M2M dependencies with deferred insertion."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "fixtures",
            nargs="+",
            help="Paths to NDJSON fixture files",
        )

    def handle(self, *args, **options):
        from file_system.models import File, FileType

        fixtures = options["fixtures"]
        all_objects = []
        fixture_pks_by_model = defaultdict(set)

        # --- Step 0: load all objects from NDJSON fixtures ---
        for fixture_path in fixtures:
            self.stdout.write(f"Reading fixture: {fixture_path}")
            with open(fixture_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # Wrap single-line JSON object for deserialize
                        for obj in deserialize("json", f"[{line}]"):
                            all_objects.append(obj)
                            fixture_pks_by_model[obj.object.__class__].add(obj.object.pk)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error parsing line {line_num} of {fixture_path}: {e}")
                        )

        self.stdout.write(f"Total objects to process: {len(all_objects)}\n")

        # Prefetch existing PKs
        existing_pks = {model: set(model.objects.values_list("pk", flat=True)) for model in fixture_pks_by_model}
        inserted_pks = {model: set() for model in fixture_pks_by_model}
        deferred_m2m = []

        # --- Step 0.5: insert File objects first ---
        try:
            placeholder_type, _ = FileType.objects.get_or_create(name="placeholder")
            file_objects = [obj for obj in all_objects if obj.object.__class__.__name__ == "File"]

            for obj in file_objects:
                model = obj.object.__class__
                pk = obj.object.pk
                if pk in existing_pks.get(model, set()):
                    self.stdout.write(self.style.WARNING(f"Skipping File({pk}) — already exists (PK)"))
                    continue
                try:
                    with transaction.atomic():
                        # Ensure placeholder file_type is used if missing
                        if not getattr(obj.object, "file_type", None):
                            obj.object.file_type = placeholder_type
                        obj.save()
                        inserted_pks[model].add(pk)
                        self.stdout.write(self.style.SUCCESS(f"Inserted File({pk})"))
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f"Failed to insert File({pk}): {e}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[WARN] Could not pre-insert File objects: {e}"))

        # --- Helper functions ---
        def exists_by_unique_fields(obj):
            """Check whether object with unique field values already exists."""
            model = obj.object.__class__
            qs = model.objects.all()

            # Single-field unique constraints
            filters = {f.name: getattr(obj.object, f.attname)
                       for f in model._meta.fields
                       if f.unique and getattr(obj.object, f.attname) is not None}
            if filters and qs.filter(**filters).exists():
                return True

            # Multi-field unique_together constraints
            for unique_fields in model._meta.unique_together:
                ufilters = {f: getattr(obj.object, f) for f in unique_fields if getattr(obj.object, f) is not None}
                if len(ufilters) == len(unique_fields) and qs.filter(**ufilters).exists():
                    return True

            return False

        def is_available(rel_model, rel_pk):
            """Check if related PK is already in DB or inserted."""
            return rel_pk in inserted_pks.get(rel_model, set()) or rel_pk in existing_pks.get(rel_model, set())

        # --- Step 1: multi-pass insert loop for all remaining objects ---
        pending = [obj for obj in all_objects if obj.object.__class__.__name__ != "File"]
        inserted, skipped = 0, 0

        while pending:
            remaining = []
            for obj in pending:
                model = obj.object.__class__
                pk = obj.object.pk

                # Skip if PK exists
                if pk in existing_pks.get(model, set()):
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {model.__name__}({pk}) — already exists (PK)")
                    )
                    continue

                # Skip if unique constraint exists
                if exists_by_unique_fields(obj):
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {model.__name__}({pk}) — unique constraint conflict")
                    )
                    continue

                # Check FK dependencies
                missing = []
                for field in model._meta.fields:
                    if field.is_relation and field.related_model:
                        rel_pk = getattr(obj.object, field.attname, None)
                        if rel_pk and not is_available(field.related_model, rel_pk):
                            missing.append(f"{field.related_model.__name__}({rel_pk})")

                # Check M2M dependencies and clear for deferred assignment
                m2m_data = {}
                for m2m_field in model._meta.many_to_many:
                    try:
                        rel_pks = [rel.pk for rel in getattr(obj.object, m2m_field.name).all()]
                        m2m_data[m2m_field.name] = rel_pks
                        for rel_pk in rel_pks:
                            if not is_available(m2m_field.related_model, rel_pk):
                                missing.append(f"{m2m_field.related_model.__name__}({rel_pk}) [M2M:{m2m_field.name}]")
                        getattr(obj.object, m2m_field.name).clear()
                    except Exception:
                        continue

                if missing:
                    remaining.append(obj)
                    self.stdout.write(
                        self.style.WARNING(
                            f"Deferring {model.__name__}({pk}) — missing dependencies: {', '.join(missing)}"
                        )
                    )
                    continue

                # Resolve FK objects
                for field in model._meta.fields:
                    if field.is_relation and field.related_model:
                        rel_pk = getattr(obj.object, field.attname, None)
                        if rel_pk and is_available(field.related_model, rel_pk):
                            try:
                                real_obj = field.related_model.objects.get(pk=rel_pk)
                                setattr(obj.object, field.name, real_obj)
                            except field.related_model.DoesNotExist:
                                pass

                # Save object
                try:
                    with transaction.atomic():
                        obj.save()
                        inserted_pks[model].add(pk)
                        self.stdout.write(self.style.SUCCESS(f"Inserted {model.__name__}({pk})"))

                    # Defer M2M assignment
                    for field_name, rel_pks in m2m_data.items():
                        if rel_pks:
                            deferred_m2m.append((obj.object, field_name, rel_pks))

                    inserted += 1

                except IntegrityError as e:
                    remaining.append(obj)
                    self.stdout.write(self.style.ERROR(f"Failed to insert {model.__name__}({pk}): {e}"))

            if len(remaining) == len(pending):
                unresolved = [f"{o.object.__class__.__name__}({o.object.pk})" for o in remaining]
                raise IntegrityError(f"Could not resolve dependencies: {', '.join(unresolved)}")

            pending = remaining  # Retry deferred objects

        # --- Step 2: assign deferred M2M ---
        for instance, field_name, rel_pks in deferred_m2m:
            getattr(instance, field_name).set(rel_pks)
            self.stdout.write(self.style.SUCCESS(
                f"Assigned M2M for {instance.__class__.__name__}({instance.pk}) field '{field_name}' -> {rel_pks}"
            ))

        self.stdout.write(self.style.SUCCESS(f"\nDone: {inserted} inserted, {skipped} skipped"))
