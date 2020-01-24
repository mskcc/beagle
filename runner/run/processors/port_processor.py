import uuid
import copy
import logging
from enum import Enum
from runner.run.processors.uri_helper import UriHelper
from runner.exceptions import PortProcessorException, UriParserException


class PortAction(Enum):
    CONVERT_TO_BID = 0
    FIX_DB_VALUES = 99 # Temporary for fixing values in DB
logger = logging.getLogger(__name__)

class PortProcessor(object):


    @staticmethod
    def process_files(port_value, action, file_list=None):
        if isinstance(port_value, list):
            res = []
        elif isinstance(port_value, dict):
            res = {}
        else:
            return port_value
        return PortProcessor._resolve_object(port_value, res, action, file_list)

    @staticmethod
    def _resolve_object(value, result, action, file_list):
        if isinstance(value, dict):
            if PortProcessor.is_file(value):
                result = PortProcessor.process_file(value, action, file_list)
                return result
            else:
                for k, v in value.items():
                    result[k] = PortProcessor.process_files(v, action, file_list)
                return result
        elif isinstance(value, list):
            for item in value:
                result.append(PortProcessor.process_files(item, action, file_list))
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
    def process_file(file_obj, action, file_list):
        if action == PortAction.CONVERT_TO_BID:
            return PortProcessor._update_location_to_bid(file_obj, file_list)
        if action == PortAction.FIX_DB_VALUES:
            return PortProcessor._fix_locations_in_db(file_obj, file_list)
        else:
            raise PortProcessorException('Unknown PortProcessor action: %s' % action)

    @staticmethod
    def _update_location_to_bid(val, file_list):
        file_obj = copy.deepcopy(val)
        location = val.get('location')
        bid = UriHelper.get_file_id(location)
        file_obj['location'] = 'bid://%s' % bid
        if file_obj.get('path'):
            file_obj.pop('path')
        if file_list is not None:
            file_list.append('bid://%s' % bid)
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
        if location.startswith('/'):
            location = 'juno://%s' % location
        elif PortProcessor.is_uuid(location):
            location = 'bid://%s' % location
        elif not location.startswith('juno://') and not location.startswith('bid:/'):
            print("Couldn't fix value: %s" % file_obj)
            return file_obj
        try:
            bid = UriHelper.get_file_id(location)
        except UriParserException as e:
            print("Couldn't fix value: %s. File doesn't exist" % file_obj)
            return file_obj
        file_obj['location'] = 'bid://%s' % bid
        if file_obj.get('path'):
            file_obj.pop('path')
        if file_list is not None:
            file_list.append('bid://%s' % bid)
        return file_obj

    @staticmethod
    def _collect_files(val):
        pass


def list_files(inp):
    result_map = {}
    for port in inp:
        name = port['fields']['name']
        file_values = []
        PortProcessor.process_files(port['fields']['db_value'], PortAction.CONVERT_TO_BID, file_values)
        result_map[name] = file_values
    return result_map
