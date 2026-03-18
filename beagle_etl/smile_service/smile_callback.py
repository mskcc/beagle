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
            msg.gene_panel = data_dict.get(settings.RECIPE_METADATA_KEY)
        elif message.subject == settings.METADB_NATS_REQUEST_UPDATE:
            if isinstance(data_dict, list) and len(data_dict) > 0:
                last_item = data_dict[-1]
                msg.request_id = last_item.get(settings.REQUEST_ID_METADATA_KEY)
                # Try to extract recipe from nested requestMetadataJson
                request_metadata_json = last_item.get("requestMetadataJson")
                if request_metadata_json:
                    try:
                        request_metadata = json.loads(request_metadata_json)
                        msg.gene_panel = request_metadata.get(settings.RECIPE_METADATA_KEY)
                    except:
                        pass  # If parsing fails, gene_panel remains None
        elif message.subject == settings.METADB_NATS_SAMPLE_UPDATE:
            msg.request_id = data_dict["latestSampleMetadata"][settings.REQUEST_ID_METADATA_KEY]
            msg.gene_panel = data_dict["latestSampleMetadata"][settings.RECIPE_METADATA_KEY]
        msg.save()
    except Exception as e:
        logger.error(e)
