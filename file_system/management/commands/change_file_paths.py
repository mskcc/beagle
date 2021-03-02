from file_system.models import File
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Update file paths'

    def add_arguments(self, parser):
        parser.add_argument('from', type=str)
        parser.add_argument('to', type=str)

    def handle(self, *args, **options):
        from_prefix = options['from']
        to_prefix = options['to']
        files = File.objects.filter(path__startswith=from_prefix).all()
        print("Number of files %s" % len(files))
        for f in files:
            f.path = f.path.replace(from_prefix, to_prefix)
            f.save(update_fields=["path"])
