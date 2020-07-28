import os
import uuid
import copy
import logging
from enum import Enum
from pathlib import Path
from runner.run.processors.file_processor import FileProcessor
from runner.exceptions import PortProcessorException, FileConflictException, FileHelperException
from notifier.tasks import send_notification
from notifier.events import UploadAttachmentEvent

logger = logging.getLogger(__name__)


class PortAction(Enum):
    CONVERT_TO_BID = 0
    CONVERT_TO_PATH = 1
    REGISTER_OUTPUT_FILES = 2
    SEND_AS_NOTIFICATION = 3
    CONVERT_TO_CWL_FORMAT = 4
    FIX_DB_VALUES = 99 # Temporary for fixing values in DB


class PortProcessor(object):

    @staticmethod
    def process_files(port_value, action, **kwargs):
        if isinstance(port_value, list):
            res = []
        elif isinstance(port_value, dict):
            res = {}
        else:
            return port_value
        return PortProcessor._resolve_object(port_value, res, action, **kwargs)

    @staticmethod
    def _resolve_object(value, result, action, **kwargs):
        if isinstance(value, dict):
            if PortProcessor.is_file(value):
                result = PortProcessor._process_file(value, action, **kwargs)
                return result
            else:
                for k, v in value.items():
                    result[k] = PortProcessor.process_files(v, action, **kwargs)
                return result
        elif isinstance(value, list):
            for item in value:
                result.append(PortProcessor.process_files(item, action, **kwargs))
            return result
        else:
            return value

    @staticmethod
    def is_uuid(val):
        try:
            val = uuid.UUID(val)
        except ValueError:
            return False
        return True

    @staticmethod
    def is_file(val):
        return True if val.get('class') and val.get('class') == 'File' else False

    @staticmethod
    def _process_file(file_obj, action, **kwargs):
        if action == PortAction.CONVERT_TO_BID:
            return PortProcessor._update_location_to_bid(file_obj, kwargs.get('file_list'))
        if action == PortAction.FIX_DB_VALUES:
            return PortProcessor._fix_locations_in_db(file_obj, kwargs.get('file_list'))
        if action == PortAction.CONVERT_TO_PATH:
            return PortProcessor._convert_to_path(file_obj)
        if action == PortAction.CONVERT_TO_CWL_FORMAT:
            return PortProcessor._covert_to_cwl_format(file_obj)
        if action == PortAction.REGISTER_OUTPUT_FILES:
            return PortProcessor._register_file(file_obj,
                                                kwargs.get('size'),
                                                kwargs.get('group_id'),
                                                kwargs.get('metadata'),
                                                kwargs.get('file_list'))
        if action == PortAction.SEND_AS_NOTIFICATION:
            return PortProcessor._send_as_notification(file_obj, kwargs.get('job_group'))
        else:
            raise PortProcessorException('Unknown PortProcessor action: %s' % action)

    @staticmethod
    def _update_location_to_bid(val, file_list):
        file_obj = copy.deepcopy(val)
        location = val.get('location')
        if not location and val.get('contents'):
            logger.debug("Processing file literal %s", str(val))
            return val
        bid = FileProcessor.get_file_id(location)
        file_obj['location'] = 'bid://%s' % bid
        secondary_files = file_obj.pop('secondaryFiles', [])
        secondary_file_list = []
        secondary_files_obj = PortProcessor.process_files(secondary_files,
                                                          PortAction.CONVERT_TO_BID,
                                                          file_list=secondary_file_list)
        if secondary_files_obj:
            file_obj['secondaryFiles'] = secondary_files_obj
        if file_obj.get('path'):
            file_obj.pop('path')
        if file_list is not None:
            file_list.append('bid://%s' % bid)
            file_list.extend([f['location'] for f in secondary_files_obj])
        return file_obj

    @staticmethod
    def _convert_to_path(val):
        file_obj = copy.deepcopy(val)
        location = file_obj.pop('location', None)
        if not location and val.get('contents'):
            logger.debug("Processing file literal %s", str(val))
            return val
        try:
            path = FileProcessor.get_file_path(location)
        except FileHelperException as e:
            raise PortProcessorException('File %s not found' % location)
        secondary_files = file_obj.pop('secondaryFiles', [])
        secondary_files_value = PortProcessor.process_files(secondary_files,
                                                                 PortAction.CONVERT_TO_PATH)
        if secondary_files_value:
            file_obj['secondaryFiles'] = secondary_files_value
        file_obj['path'] = path
        return file_obj

    @staticmethod
    def _covert_to_cwl_format(val):
        file_obj = copy.deepcopy(val)
        location = file_obj.pop('location',None)
        if location:
            try:
                file_db_object = FileProcessor.get_file_obj(location)
            except FileHelperException as e:
                raise PortProcessorException('File %s not found' % location)
            path = file_db_object.path
            path_obj = Path(path)
            checksum = FileProcessor.get_file_checksum(file_db_object)
            if checksum:
                file_obj['checksum'] = checksum
            size = FileProcessor.get_file_size(file_db_object)
            if size:
                file_obj['size'] = size
            file_obj['basename'] = path_obj.name
            file_obj['nameext'] = path_obj.suffix
            file_obj['nameroot'] = path_obj.stem
            file_obj['path'] = path
        secondary_files = file_obj.pop('secondaryFiles', [])
        secondary_files_value = PortProcessor.process_files(secondary_files,
                                                                 PortAction.CONVERT_TO_CWL_FORMAT)
        if secondary_files_value:
            file_obj['secondaryFiles'] = secondary_files_value

        return file_obj

    @staticmethod
    def _fix_locations_in_db(val, file_list):
        """
        Temporary method for fixing Values in DB
        :param val:
        :param file_list:
        :return:
        """
        file_obj = copy.deepcopy(val)
        location = val.get('location')
        if not location:
            location = val.get('path')
        if not location:
            print("Couldn't fix value: %s. File doesn't exist" % file_obj)
            return file_obj
        if location.startswith('/'):
            location = 'juno://%s' % location
        elif PortProcessor.is_uuid(location):
            location = 'bid://%s' % location
        elif not location.startswith('juno://') and not location.startswith('bid:/'):
            print("Couldn't fix value: %s" % file_obj)
            return file_obj
        try:
            bid = FileProcessor.get_file_id(location)
        except FileHelperException as e:
            print("Couldn't fix value: %s. File doesn't exist" % file_obj)
            return file_obj
        file_obj['location'] = 'bid://%s' % bid
        if file_obj.get('path'):
            file_obj.pop('path')
        if file_list is not None:
            file_list.append('bid://%s' % bid)
        return file_obj

    @staticmethod
    def _register_file(val, size, group_id, metadata, file_list):
        file_obj = copy.deepcopy(val)
        file_obj.pop("basename", None)
        file_obj.pop("nameroot", None)
        file_obj.pop("nameext", None)
        uri = file_obj.pop('location', None)
        checksum = file_obj.pop("checksum", None)
        try:
            file_obj_db = FileProcessor.create_file_obj(uri, size, checksum, group_id, metadata)
        except FileConflictException as e:
            logger.warning(str(e))
            file_obj_db = FileProcessor.get_file_obj(uri)
            # TODO: Check what to do in case file already exist in DB. Note: This should never happen
            # raise PortProcessorException(e)
        secondary_files = file_obj.pop('secondaryFiles', [])
        secondary_file_list = []
        secondary_files_obj = PortProcessor.process_files(secondary_files,
                                                          PortAction.REGISTER_OUTPUT_FILES,
                                                          group_id=group_id,
                                                          metadata=metadata,
                                                          file_list=secondary_file_list)
        if secondary_files_obj:
            file_obj['secondaryFiles'] = secondary_files_obj
        file_obj['location'] = FileProcessor.get_bid_from_file(file_obj_db)
        if file_list is not None:
            file_list.append('bid://%s' % FileProcessor.get_bid_from_file(file_obj_db))
            file_list.extend([f['location'] for f in secondary_files_obj])
        return file_obj

    @staticmethod
    def _send_as_notification(val, job_group):
        uri = val.get('location')
        path = FileProcessor.parse_path_from_uri(uri)
        file_name = os.path.basename(path)
        if job_group:
            event = UploadAttachmentEvent(str(job_group.id), file_name, path, download=True)
            send_notification.delay(event.to_dict())
        logger.info("Can't upload file:%s. JobGroup not specified", path)
        return val
