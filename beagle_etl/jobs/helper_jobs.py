import os
import logging
from time import sleep
from celery import shared_task
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


def check_file_permissions(path):
    if not os.access(path, os.R_OK):
        raise FailedToCopyFilePermissionDeniedException()


def R1_or_R2(filename):
    reversed_filename = "".join(reversed(filename))
    R1_idx = reversed_filename.find("1R")
    R2_idx = reversed_filename.find("2R")
    if R1_idx == -1 and R2_idx == -1:
        return "UNKNOWN"
    elif R1_idx > 0 and R2_idx == -1:
        return "R1"
    elif R2_idx > 0 and R1_idx == -1:
        return "R2"
    elif R1_idx > 0 and R2_idx > 0:
        if R1_idx < R2_idx:
            return "R1"
        else:
            return "R2"
    return "UNKNOWN"


def check_file_exist(path):
    """
    Confirm file is registered correctly
    """
    file_cnt = FileRepository.filter(path=path, file_group=settings.IMPORT_FILE_GROUP).count()
    if file_cnt == 0:
        raise FailedToRegisterFileException("File %s not registered", path)
    elif file_cnt > 1:
        raise DuplicatedFilesException("Duplicated file %s", path)


def fix_path_iris(path):
    """
    Helper function necessary only for IRIS because the SMILEMessage paths are not same as mount paths
    """
    return path.replace(settings.FASTQ_DEFAULT_LOCATION_PREFIX, settings.FASTQ_IRIS_LOCATION_PREFIX)


@shared_task
def calculate_checksum(file_id):
    try:
        f = File.objects.get(id=file_id)
    except File.DoesNotExist:
        logger.error("Failed to calculate checksum. Error: File %s not found", file_id)
        raise FailedToCalculateChecksum("Failed to calculate checksum. Error: File %s not found", file_id)
    try:
        checksum = sha1(f.original_path)
    except FailedToCalculateChecksum as e:
        logger.error(f"Failed to calculate checksum for file: {file_id}: {f.original_path}")
        raise FailedToCalculateChecksum("Failed to calculate checksum. Error: File %s not found", file_id)
    f.checksum = checksum
    f.save(update_fields=["checksum"])
