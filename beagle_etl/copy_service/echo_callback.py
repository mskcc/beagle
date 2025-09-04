import logging
from beagle_etl.models import SMILEMessage, CopyFileTask, CopyFileStatus


logger = logging.getLogger()


def echo_callback(message):
    try:
        logger.debug(f"Processing notification: {message.to_json()}")
        task = CopyFileTask.objects.get(id=message.id)
        if message.status == "success":
            task.set_completed(message.message)
        if message.status == "fail":
            task.set_failed()
    except Exception as e:
        logger.error(f"Error processing notification: {e}")
        raise
