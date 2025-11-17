import os
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers import deserialize


class Command(BaseCommand):
    help = "Load a JSON fixture but skip objects that already exist (by PK)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--in",
            dest="in_file",
            required=True,
            help="Path to the JSON fixture file",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="If given, update existing objects instead of skipping them",
        )

    def handle(self, *args, **options):
        fixture_path = options["in_file"]
        do_update = options["update"]

        if not os.path.exists(fixture_path):
            raise CommandError(f"Fixture not found: {fixture_path}")

        with open(fixture_path, "r") as f:
            try:
                objects = list(deserialize("json", f))
            except Exception as e:
                raise CommandError(f"Failed to deserialize fixture: {e}")

        created, skipped, updated = 0, 0, 0

        for obj in objects:
            model = obj.object.__class__
            pk = obj.object.pk

            if not model.objects.filter(pk=pk).exists():
                obj.save()
                created += 1
            else:
                if do_update:
                    obj.save(force_update=True)
                    updated += 1
                else:
                    skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported fixture {fixture_path}: " f"{created} created, {updated} updated, {skipped} skipped"
            )
        )
