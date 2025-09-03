import os
import logging
from time import sleep
from django.conf import settings
from file_system.models import File
from file_system.repository import FileRepository
from file_system.helper.checksum import sha1, FailedToCalculateChecksum
from beagle_etl.exceptions import (
    FailedToCopyFilePermissionDeniedException,
    DuplicatedFilesException,
    FailedToRegisterFileException,
    FailedToLocateTheFileException,
)


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
            f.save(update_fields=["checksum"])
        except FailedToCalculateChecksum as e:
            logger.info("Failed to calculate checksum. Error:%s", f.path)
    return []


def check_file_permissions(path):
    if not os.access(path, os.R_OK):
        raise FailedToCopyFilePermissionDeniedException()


def check_file_exist(path):
    """
    Confirm file is registered correctly
    """
    file_cnt = FileRepository.filter(path=path, file_group=settings.IMPORT_FILE_GROUP).count()
    if file_cnt == 0:
        raise FailedToRegisterFileException("File %s not registered", path)
    elif file_cnt > 1:
        raise DuplicatedFilesException("Duplicated file %s", path)


def locate_file(path):
    if os.path.exists(path):
        return path
    for k, v in settings.MAPPING.items():
        if path.startswith(k):
            for r in v:
                check_path = path.replace(k, r)
                if os.path.exists(check_path):
                    return check_path
    raise FailedToLocateTheFileException(f"Unable to locate file: {path} on file system")

def fix_path_iris(path):
    return path.replace(settings.FASTQ_DEFAULT_LOCATION_PREFIX, settings.FASTQ_IRIS_LOCATION_PREFIX)
