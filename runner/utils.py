"""
Utility and helper functions for use in the Runner app
"""
import urllib

class InvalidBIDError(Exception):
    pass

class DbValuesLackClassKeyError(Exception):
    pass

class UnknownSchemaError(Exception):
    pass

def has_bid(location):
    """
    Check if a location string has a valid Beagle database ID

    Parameters
    ----------
    location: str
        a URI string

    Returns
    -------
    bool
        True or False if the given string has a valid Beagle database ID
    """
    parts = urllib.parse.urlsplit(location)
    scheme = parts.scheme
    if scheme == 'bid':
        return(True)
    else:
        return(False)

def get_BID_from_location(location):
    """
    Return a valid Beagle database id from a location URI string

    Parameters
    ----------
    location: str
        a URI string

    Returns
    -------
    str
        string representing the Beagle database ID
    """
    if not has_bid(location):
        raise InvalidBIDError
    parts = urllib.parse.urlsplit(location)
    bid = parts.netloc
    if bid == '':
        raise InvalidBIDError("location is not a valid Beagle ID: {}".format(location))
    return(bid)


def get_bids_from_Port_db_values(db_values):
    """
    Get all the bids from a 'db_values' sub-entry, which may be a dict or list of dicts

    Parameters
    ----------
    db_values: dict | list
        a dict or list of dicts representing Port model 'db_values'
    """
    bids = []
    if isinstance(db_values, dict):
        if 'class' in db_values:
            if db_values['class'] == 'File':
                bid = get_BID_from_location(db_values['location'])
                bids.append(bid)
            else:
                # TODO: what to do here?
                pass
        else:
            raise DbValuesLackClassKeyError("WARNING: db_values does not have key 'class': {}".format(db_values))
    elif isinstance(db_values, list):
        for db_value in db_values:
            if 'class' in db_value:
                if db_value['class'] == 'File':
                    bid = get_BID_from_location(db_value['location'])
                    bids.append(bid)
                else:
                    # TODO: what to do here?
                    pass
            else:
                raise DbValuesLackClassKeyError("WARNING: db_values does not have key 'class': {}".format(db_value))
    return(bids)


def get_all_bids_from_Port(instance):
    """
    Get all the bids from a Port instance

    Parameters
    ----------
    instance: Port
        a Django Port model instance

    Returns
    -------
    list
        a list of character strings of the Beagle File database id's associated with the Port instances
    """
    file_ids = []
    schema_type = instance.schema.get('type')
    schema_items = instance.schema.get('items')
    db_values = instance.__dict__['db_value']
    if schema_type == ['null', 'array']:
        for bid in get_bids_from_Port_db_values(db_values):
            file_ids.append(bid)
    elif schema_type == 'array':
        for db_value in db_values:
            for bid in get_bids_from_Port_db_values(db_value):
                file_ids.append(bid)
    else:
        # TODO: what to do here?
        raise UnknownSchemaError("unrecognized 'schema' value for: {}".format(db_values))
    return(file_ids)
