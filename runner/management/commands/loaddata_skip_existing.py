# runner/management/commands/loaddata_skip_existing.py

import json
from django.core.management.base import BaseCommand
from django.core.serializers import deserialize
from django.db import transaction, IntegrityError


class Command(BaseCommand):
    help = "Load fixtures but skip objects that already exist. Supports dry-run."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixtures",
            nargs="+",
            help="Paths to fixture files (JSON)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the load without saving anything",
        )

    def handle(self, *args, **options):
        fixtures = options["fixtures"]
        dry_run = options["dry_run"]

        # Load all objects from fixtures
        all_objects = []
        for fixture_path in fixtures:
            self.stdout.write(f"Reading fixture: {fixture_path}")
            with open(fixture_path, "r") as f:
                objs = list(deserialize("json", f.read()))
                self.stdout.write(f"  Found {len(objs)} objects")
                all_objects.extend(objs)

        self.stdout.write(f"Total objects to process: {len(all_objects)}\n")

        # Collect all PKs from the fixture upfront
        fixture_pks_by_model = {}
        for obj in all_objects:
            model = obj.object.__class__
            fixture_pks_by_model.setdefault(model, set()).add(obj.object.pk)

        inserted_pks = {m: set() for m in fixture_pks_by_model}

        pending = all_objects[:]
        inserted, skipped, deferred = 0, 0, 0

        def is_available(related_model, rel_pk):
            return (
                related_model.objects.filter(pk=rel_pk).exists()
                or rel_pk in inserted_pks.get(related_model, set())
                or rel_pk in fixture_pks_by_model.get(related_model, set())
            )

        while pending:
            remaining = []
            for obj in pending:
                model = obj.object.__class__
                pk = obj.object.pk

                # Already exists in DB
                if model.objects.filter(pk=pk).exists():
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"{'[DRY RUN] ' if dry_run else ''}" f"Skipped {model.__name__}({pk}) (already exists)"
                        )
                    )
                    continue

                # Check for missing dependencies
                missing = []
                for field in model._meta.fields:
                    if field.is_relation:
                        rel_pk = getattr(obj.object, field.attname, None)
                        if rel_pk and not is_available(field.related_model, rel_pk):
                            missing.append(f"{field.related_model.__name__}({rel_pk})")

                if missing:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{'[DRY RUN] ' if dry_run else ''}"
                            f"Deferring {model.__name__}({pk}), missing: {', '.join(missing)}"
                        )
                    )
                    remaining.append(obj)
                    continue

                # Insert or simulate
                if dry_run:
                    inserted += 1
                    inserted_pks[model].add(pk)
                    self.stdout.write(self.style.NOTICE(f"[DRY RUN] Would insert {model.__name__}({pk})"))
                else:
                    try:
                        with transaction.atomic():
                            obj.save()
                        inserted += 1
                        inserted_pks[model].add(pk)
                        self.stdout.write(self.style.SUCCESS(f"Inserted {model.__name__}({pk})"))
                    except IntegrityError as e:
                        msg = str(e)
                        if "duplicate key value violates unique constraint" in msg:
                            skipped += 1
                            self.stdout.write(self.style.WARNING(f"Skipped {model.__name__}({pk}) (already exists)"))
                        elif "violates foreign key constraint" in msg:
                            self.stdout.write(
                                self.style.WARNING(f"Deferring {model.__name__}({pk}), missing (detected at save)")
                            )
                            remaining.append(obj)
                        else:
                            raise

            if len(remaining) == len(pending):
                # Could not resolve further
                if dry_run:
                    deferred += len(remaining)
                    for obj in remaining:
                        model = obj.object.__class__
                        pk = obj.object.pk
                        missing = []
                        for field in model._meta.fields:
                            if field.is_relation:
                                rel_pk = getattr(obj.object, field.attname, None)
                                if rel_pk and not is_available(field.related_model, rel_pk):
                                    missing.append(f"{field.related_model.__name__}({rel_pk})")
                        self.stdout.write(
                            self.style.WARNING(
                                f"[DRY RUN] Would defer {model.__name__}({pk}), missing: {', '.join(missing) or 'unknown'}"
                            )
                        )
                    break
                else:
                    raise IntegrityError(f"Could not resolve dependencies, still {len(remaining)} pending")

            pending = remaining

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: {inserted} inserted, {skipped} skipped"
                + (f", {deferred} deferred (dry run)" if dry_run else "")
            )
        )
