# runner/management/commands/loaddata_skip_existing.py

from django.core.management.base import BaseCommand
from django.core.serializers import deserialize
from django.db import transaction, IntegrityError


class Command(BaseCommand):
    help = (
        "Load fixtures but skip objects that already exist. "
        "Handles PK and unique constraints, FK and M2M dependencies."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "fixtures",
            nargs="+",
            help="Paths to fixture files (JSON)",
        )

    def handle(self, *args, **options):
        fixtures = options["fixtures"]

        fixture_pks_by_model = {}
        all_objects = []

        for fixture_path in fixtures:
            self.stdout.write(f"Reading fixture: {fixture_path}")
            with open(fixture_path, "r") as f:
                for line in f:
                    if line.strip():
                        for obj in deserialize("json", line):
                            all_objects.append(obj)
                            model = obj.object.__class__
                            fixture_pks_by_model.setdefault(model, set()).add(obj.object.pk)

        self.stdout.write(f"Total objects to process: {len(all_objects)}\n")

        # Collect all PKs from fixture
        fixture_pks_by_model = {}
        for obj in all_objects:
            model = obj.object.__class__
            fixture_pks_by_model.setdefault(model, set()).add(obj.object.pk)

        # Prefetch existing PKs from DB
        existing_pks = {model: set(model.objects.values_list("pk", flat=True)) for model in fixture_pks_by_model}

        inserted_pks = {model: set() for model in fixture_pks_by_model}
        deferred_m2m = []

        pending = all_objects[:]
        inserted, skipped = 0, 0

        def exists_by_unique_fields(obj):
            model = obj.object.__class__
            qs = model.objects.all()
            filters = {}
            for field in model._meta.fields:
                if field.unique:
                    value = getattr(obj.object, field.attname)
                    if value is not None:
                        filters[field.name] = value
            if filters:
                return qs.filter(**filters).exists()
            return False

        def is_available(related_model, rel_pk):
            return rel_pk in inserted_pks.get(related_model, set()) or rel_pk in existing_pks.get(related_model, set())

        while pending:
            remaining = []
            for obj in pending:
                model = obj.object.__class__
                pk = obj.object.pk

                # Skip if PK or unique fields already exist
                if pk in existing_pks.get(model, set()) or exists_by_unique_fields(obj):
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"Skipped {model.__name__}({pk}) (already exists or unique conflict)")
                    )
                    continue

                # Check FK dependencies
                missing = []
                for field in model._meta.fields:
                    if field.is_relation and not field.many_to_one and not field.one_to_many:
                        continue
                    if field.is_relation:
                        rel_pk = getattr(obj.object, field.attname, None)
                        if rel_pk and not is_available(field.related_model, rel_pk):
                            missing.append(f"{field.related_model.__name__}({rel_pk})")

                # Check M2M dependencies (deferred, but must exist before assignment)
                for m2m_field in model._meta.many_to_many:
                    rel_pks = [rel.pk for rel in getattr(obj.object, m2m_field.name).all()]
                    for rel_pk in rel_pks:
                        if not is_available(m2m_field.related_model, rel_pk):
                            missing.append(f"{m2m_field.related_model.__name__}({rel_pk}) [M2M:{m2m_field.name}]")

                if missing:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Deferring {model.__name__}({pk}), missing dependencies: {', '.join(missing)}"
                        )
                    )
                    remaining.append(obj)
                    continue

                for field in model._meta.fields:
                    if field.is_relation and not field.many_to_one and not field.one_to_many:
                        continue
                    if field.is_relation:
                        rel_pk = getattr(obj.object, field.attname, None)
                        if rel_pk and rel_pk in existing_pks.get(field.related_model, set()):
                            try:
                                real_obj = field.related_model.objects.get(pk=rel_pk)
                                setattr(obj.object, field.name, real_obj)
                            except field.related_model.DoesNotExist:
                                pass
                
                m2m_data = {}
                for m2m_field in model._meta.many_to_many:
                    m2m_data[m2m_field.name] = [rel.pk for rel in getattr(obj.object, m2m_field.name).all()]
                    getattr(obj.object, m2m_field.name).clear() 
                if model.__name__ == "Port":
                    try:
                        from file_system.models import File  # adjust import path if needed
                        file_id = getattr(obj.object, "file_id", None)
                        if file_id and not File.objects.filter(id=file_id).exists():
                            self.stdout.write(
                                self.style.WARNING(f"[FIX] Creating placeholder File {file_id} for Port {pk}")
                            )
                            File.objects.create(id=file_id, path=f"MISSING_FILE_{file_id}", size=0)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"[WARN] Could not auto-create missing File: {e}")
                        )
                # Save object
                try:
                    with transaction.atomic():
                        obj.save()
                        inserted_pks[model].add(pk)

                    # Defer M2M until all inserts are complete
                    for m2m_field in model._meta.many_to_many:
                        rel_pks = [rel.pk for rel in getattr(obj.object, m2m_field.name).all()]
                        if rel_pks:
                            deferred_m2m.append((obj.object, m2m_field.name, rel_pks))

                    inserted += 1
                    self.stdout.write(self.style.SUCCESS(f"Inserted {model.__name__}({pk})"))
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f"Failed to insert {model.__name__}({pk}): {e}"))

            if len(remaining) == len(pending):
                # Cannot resolve dependencies further
                unresolved = [f"{obj.object.__class__.__name__}({obj.object.pk})" for obj in remaining]
                raise IntegrityError(
                    f"Could not resolve dependencies for the following objects: {', '.join(unresolved)}"
                )

            pending = remaining

        # Assign deferred M2M relationships now that everything exists
        for instance, field_name, rel_pks in deferred_m2m:
            getattr(instance, field_name).set(rel_pks)

        self.stdout.write(self.style.SUCCESS(f"\nDone: {inserted} inserted, {skipped} skipped"))
