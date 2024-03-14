import json
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from beagle_etl.jobs.metadb_jobs import new_request
from beagle_etl.models import SMILEMessage, SmileMessageStatus


class Command(BaseCommand):
    help = "Import data from SMILE"

    def add_arguments(self, parser):
        parser.add_argument("--request-id", type=str)

    def handle(self, *args, **options):
        request_id = options["request_id"]
        response = requests.get(f"http://smile.mskcc.org:3000/request/{request_id}")
        if response.status_code == 200:
            print(f"Importing {request_id}")
            smile_message = SMILEMessage.objects.create(request_id=request_id,
                                                        topic=settings.METADB_NATS_NEW_REQUEST,
                                                        message=json.dumps(response.json()),
                                                        status=SmileMessageStatus.PENDING)
            new_request(str(smile_message.id))
            smile_message.refresh_from_db()
            if smile_message.status == SmileMessageStatus.COMPLETED:
                print(f"Successfully imported request {request_id}")
            else:
                print(f"Failed to import request {request_id}")
        else:
            print(f"Failed to fetch {request_id} from SMILE with error: {response.json()}")
