import json
import logging
from django.conf import settings
from beagle_etl.models import SMILEMessage


logger = logging.getLogger("smile_client")


def persist_message(message):
    try:
        msg = SMILEMessage.objects.create(topic=message.subject, message=message.data)
        data_dict = json.loads(message.data)
        if message.subject == settings.METADB_NATS_NEW_REQUEST:
            msg.request_id = data_dict.get(settings.REQUEST_ID_METADATA_KEY)
        elif message.subject == settings.METADB_NATS_REQUEST_UPDATE:
            msg.request_id = data_dict.get(settings.REQUEST_ID_METADATA_KEY)
        elif message.subject == settings.METADB_NATS_SAMPLE_UPDATE:
            msg.request_id = data_dict["latestSampleMetadata"][settings.SAMPLE_ID_METADATA_KEY]
        msg.save()
    except Exception as e:
        logger.error(e)
