import os
import logging
from time import sleep
from file_system.models import File
from file_system.helper.checksum import sha1, FailedToCalculateChecksum


logger = logging.getLogger(__name__)


def populate_file_checksums():
    logger.info("Calculating file checksum")
    files = File.objects.all()
    for f in files:
        logger.info("Processing file:%s checksum" % str(f.id))
        if not f.checksum:
            logger.debug("Calculating file:%s checksum" % str(f.id))
            try:
                checksum = sha1(f.path)
                f.checksum = checksum
                f.save()
            except FailedToCalculateChecksum as e:
                logger.info("Failed to calculate checksum. Error:%s", f.path)
            sleep(1)
    return []


def populate_file_size():
    logger.info("Populating file size")
    files = File.objects.all()
    for f in files:
        if not f.size or f.size == 0:
            try:
                f.size = os.path.getsize(f.path)
            except Exception as e:
                logger.error("Failed to get file size. Error:%s", f.path)
            sleep(1)
    return []


def calculate_file_checksum(file_id):
    logger.info("Calculate file checksum for file:%s", file_id)
    try:
        f = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return None
    else:
        try:
            checksum = sha1(f.path)
            f.checksum = checksum
            f.save(update_fields=['checksum'])
        except FailedToCalculateChecksum as e:
            logger.info("Failed to calculate checksum. Error:%s", f.path)
    return []
