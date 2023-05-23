from django.core.management.base import BaseCommand
from beagle_etl.jobs.metadb_jobs import update_sample_job


class Command(BaseCommand):
    help = "Update Sample"

    def add_arguments(self, parser):
        parser.add_argument("--smile-msg-id", type=str)

    def handle(self, *args, **options):
        smile_message_id = options["smile_msg_id"]
        print(f"Running update for {smile_message_id}")
        update_sample_job(smile_message_id)
