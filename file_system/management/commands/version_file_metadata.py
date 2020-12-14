import os
from deepdiff import DeepDiff
from django.core.management.base import BaseCommand, CommandError
from file_system.repository.file_repository import FileRepository
from django.conf import settings


class Command(BaseCommand):
    help = 'Create diff files for updated files'

    def handle(self, *args, **options):
        jira_directories = os.listdir(settings.NOTIFIER_STORAGE_DIR)
        for dir in jira_directories:
            print(dir)
            files = os.listdir(os.path.join(settings.NOTIFIER_STORAGE_DIR, dir))
            for f in files:
                self._create_metadata_versioned_files(os.path.join(settings.NOTIFIER_STORAGE_DIR, dir, f))

    def _create_metadata_versioned_files(self, filepath):
        print(filepath)
        filename = os.path.basename(filepath)
        print(filename)
        filename = filename.replace('_metadata_update.json', '')
        f = FileRepository.filter(file_name=filename).first()
        print(f)
        metadata = f.file.filemetadata_set.order_by('-created_date').all()
        print(len(metadata))
        for i in range(len(metadata) - 1):
            ddiff = DeepDiff(metadata[i + 1].metadata,
                             metadata[i].metadata,
                             ignore_order=True)
            print(ddiff)
            diff_file_name = "%s_metadata_update_%s.json" % (f.file.file_name, metadata[i].version)
            new_file = os.path.join(os.path.dirname(filepath), diff_file_name)
            print("New file name")
            print(new_file)
            with open(new_file, 'w') as fh:
                fh.write(str(ddiff))
        os.remove(filepath)
