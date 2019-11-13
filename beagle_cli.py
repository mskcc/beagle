import os
import requests
import json
import getpass
from docopt import docopt
from os.path import expanduser
from urllib.parse import urljoin


BEAGLE_ENDPOINT = os.environ.get('BEAGLE_ENDPOINT', 'http://silo:5001')


CONFIG_TEMPLATE = {
    'token': '',
    'refresh': '',
    'next': None,
    'prev': None
}


API = {
    "auth": "api-token-auth/",
    "verify": "api-token-verify/",
    "refresh": "api-token-refresh/",
    "storage": "v0/fs/storage/",
    "file-types": 'v0/fs/file-types/',
    "files": '/v0/fs/files/',
}

USAGE = """
Beagle API.

Usage:
  beagle_cli.py files create <file_path> <file_type> <file_group_id> [--metadata-path=<metadata_path>] [--size=<size>]
  beagle_cli.py files update <file_id> [--file-path=<file_path>] [--file-type=<file_type>] [--file-group=<file_group_id>] [--metadata-path=<metadata_path>] [--size=<size>]
  beagle_cli.py files list [--page-size=<page_size>] [--metadata=<metadata>]... [--file-group=<file_group>]... [--file-name=<file_name>]... [--filename-regex=<filename_regex>]
  beagle_cli.py storage create <storage_name>
  beagle_cli.py storage list
  beagle_cli.py file-types create <file_type>
  beagle_cli.py file-types list
  beagle_cli.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""


CONFIG_LOCATION = os.path.join(expanduser("~"), '.beagle.conf')


class Config(object):

    def __init__(self, token, refresh, next, prev):
        self.token = token
        self.refresh = refresh
        self.next = next
        self.prev = prev

    @classmethod
    def load(cls):
        if os.path.exists(CONFIG_LOCATION):
            with open(CONFIG_LOCATION) as config:
                config = cls(**json.load(config))
        else:
            with open(CONFIG_LOCATION, 'w') as config:
                config = cls('', '', None, None)
                config.dump()
        return config

    def set(self, key, val):
        setattr(self, key, val)
        self.dump()

    def dump(self):
        with open(CONFIG_LOCATION, 'w') as f:
            json.dump({'token': self.token, 'refresh': self.refresh, 'next': self.next, 'prev': self.prev}, f)

    def __repr__(self):
        return 'token: %s, next: %s, prev: %s' % (self.token, self.next, self.prev)


# Commands


def files_commands(arguments, config):
    if arguments.get('list'):
        return _get_files(arguments, config)
    if arguments.get('create'):
        return _create_file(arguments, config)
    if arguments.get('update'):
        return _update_file(arguments, config)


def storage_commands(arguments, config):
    if arguments.get('list'):
        return _get_storage(arguments, config)
    if arguments.get('create'):
        return _create_storage(arguments, config)


def file_types_commands(arguments, config):
    if arguments.get('list'):
        return _get_file_types_command(arguments, config)
    if arguments.get('create'):
        return _create_file_type(arguments, config)


def command(arguments, config):
    if arguments.get('files'):
        return files_commands(arguments, config)
    if arguments.get('storage'):
        return storage_commands(arguments, config)
    if arguments.get('file-types'):
        return file_types_commands(arguments, config)


# Authentication


def authenticate_command(config):
    if _check_is_authenticated(config):
        return
    while True:
        username = input("Username: ")
        if not username:
            print("Username needs to be specified")
            continue
        password = getpass.getpass("Password: ")
        if not password:
            print("Password needs to be specified")
            continue
        try:
            tokens = _authenticate(username, password)
        except Exception as e:
            print("Invalid username or password")
            continue
        else:
            config.set('token', tokens['access'])
            config.set('refresh', tokens['refresh'])
            print("Successfully authenticated")
            return


def _authenticate(username, password):
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['auth']), {"username": username, "password": password})
    if response.status_code == 200:
        return response.json()
    raise Exception


def _check_is_authenticated(config):
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['verify']), {'token': config.token})
    if response.status_code == 200:
        return True
    else:
        response = requests.post(urljoin(BEAGLE_ENDPOINT, API['refresh']), {'refresh': config.refresh})
        if response.status_code == 200:
            config.set('token', response.json()['access'])
            return True
    return False


# List commands


def _get_file_types_command(arguments, config):
    page_size = arguments.get('--page-size')
    params = dict()
    if page_size:
        params['page_size'] = page_size
    response = requests.get(urljoin(BEAGLE_ENDPOINT, API['file-types']),
                            headers={'Authorization': 'Bearer %s' % config.token}, params=params)
    response_json = json.dumps(response.json(), indent=4)
    config.set('prev', None)
    config.set('next', None)
    return response_json


def _get_storage(arguments, config):
    page_size = arguments.get('--page-size')
    params = dict()
    if page_size:
        params['page_size'] = page_size
    response = requests.get(urljoin(BEAGLE_ENDPOINT, API['storage']), headers={'Authorization': 'Bearer %s' % config.token}, params=params)
    response_json = json.dumps(response.json(), indent=4)
    _set_next_and_prev(config, response.json())
    return response_json


def _get_files(arguments, config):
    metadata = arguments.get('--metadata')
    file_group = arguments.get('--file-group')
    file_name = arguments.get('--file-name')
    filename_regex = arguments.get('--filename-regex')
    page_size = arguments.get('--page-size')
    params = dict()
    params['metadata'] = metadata
    params['file_group'] = file_group
    params['file_name'] = file_name
    params['filename_regex'] = filename_regex
    if page_size:
        params['page_size'] = page_size
    response = requests.get(urljoin(BEAGLE_ENDPOINT, API['files']), headers={'Authorization': 'Bearer %s' % config.token}, params=params)
    response_json = json.dumps(response.json(), indent=4)
    _set_next_and_prev(config, response.json())
    return response_json


def _set_next_and_prev(config, value):
    config.set('prev', value.get('previous'))
    config.set('next', value.get('next'))


def next(config):
    response = requests.get(config.next,
                            headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    _set_next_and_prev(config, response.json())
    return response_json


def prev(config):
    response = requests.get(config.prev,
                            headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    _set_next_and_prev(config, response.json())
    return response_json


# Create


def _create_file(arguments, config):
    path = arguments.get('<file_path>')
    metadata_path = arguments.get('--metadata-path')
    size = arguments.get('--size')
    metadata = {}
    if metadata_path:
        with open(metadata_path) as f:
            metadata = json.load(f)
            print(metadata)
    file_type = arguments.get('<file_type>')
    file_group_id = arguments.get('<file_group_id>')
    body = {
        "path": path,
        "metadata": json.dumps(metadata),
        "file_group_id": file_group_id,
        "file_type": file_type,
    }
    if size:
        body["size"] = size
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['files']), data=body,
                             headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    return response_json


def _create_file_type(arguments, config):
    ext = arguments.get('<file_type>')
    body = {
        "ext": ext
    }
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['file-types']), data=body,
                             headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    return response_json


def _create_storage(arguments, config):
    name = arguments.get('<storage_name>')
    body = {
        "name": name,
        "type": 0,
    }
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['storage']), data=body,
                             headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    return response_json


# Update


def _update_file(arguments, config):
    path = arguments.get('<file_path>')
    metadata_path = arguments.get('--metadata-path')
    size = arguments.get('--size')
    metadata = {}
    if metadata_path:
        with open(metadata_path) as f:
            metadata = json.load(f)
            print(metadata)
    file_type = arguments.get('<file_type>')
    file_group_id = arguments.get('<file_group_id>')
    body = {
        "path": path,
        "metadata": json.dumps(metadata),
        "file_group_id": file_group_id,
        "file_type": file_type,
    }
    if size:
        body["size"] = size
    response = requests.post(urljoin(BEAGLE_ENDPOINT, API['files']), data=body,
                             headers={'Authorization': 'Bearer %s' % config.token})
    response_json = json.dumps(response.json(), indent=4)
    return response_json


if __name__ == '__main__':
    config = Config.load()
    authenticate_command(config)
    arguments = docopt(USAGE, version='Beagle API 0.1.0')
    result = command(arguments, config)
    print(result)
    if arguments.get('list'):
        while config.next or config.prev:
            if config.next and config.prev:
                page = input("Another page (next, prev): ")
                if page == 'next':
                    result = next(config)
                    print(result)
                elif page == 'prev':
                    result = prev(config)
                    print(result)
                else:
                    break
            elif config.next and not config.prev:
                page = input("Another page (next): ")
                if page == 'next':
                    result = next(config)
                    print(result)
                else:
                    break
            elif not config.next and config.prev:
                page = input("Another page (prev): ")
                if page:
                    result = prev(config)
                    print(result)
                else:
                    break
