import uuid
import git
import os
import json
import shutil
import datetime
import subprocess
from collections import OrderedDict
from django.conf import settings


class CacheObject(object):

    def __init__(self, value):
        self.last_used = datetime.datetime.now()
        self.value = value

    def __str__(self):
        return "LastUsed: %s Object: %s" % (self.last_used, self.value)


class Cache(object):

    def __init__(self, size=20):
        self.cache = OrderedDict()
        self.cache_size = size
        self.size = 0

    def get(self, key):
        cache_object = self.cache.get(key)
        if cache_object:
            self.cache[key].last_used = datetime.datetime.now()
            return cache_object.value
        else:
            return None

    def put(self, key, val):
        if self.size == self.cache_size:
            self.cache.pop(min(self.cache, key=lambda x: self.cache[x].last_used))
            self.size = self.size - 1
        self.cache[key] = CacheObject(val)
        self.size = self.size + 1


class CWLResolver(object):

    def __init__(self, github, entrypoint, version=None):
        self.github = github
        self.entrypoint = entrypoint
        self.version = version

    def resolve(self):
        dir = self._dir_name()
        location = self.git_clone(dir)
        output_name = os.path.join(location, '%s.cwl' % str(uuid.uuid4()))
        with open(output_name, 'w') as out:
            subprocess.check_call([settings.RABIX_PATH, '-r', os.path.join(location, self.entrypoint)], stdout=out)
        with open(output_name) as f:
            pipeline = json.load(f)
        self._clanup(location)
        return pipeline

    def create_file(self):
        dir = self._dir_name()
        location = self.git_clone(dir)
        output_name = os.path.join(location, '%s.cwl' % str(uuid.uuid4()))
        with open(output_name, 'w') as out:
            subprocess.check_call([settings.RABIX_PATH, '-r', os.path.join(location, self.entrypoint)], stdout=out)
        return output_name

    def git_clone(self, location):
        git.Git(location).clone(self.github, '--branch', self.version, '--recurse-submodules')
        dirname = self._extract_dirname_from_github_link()
        return os.path.join(location, dirname)

    def _dir_name(self):
        dirname = '/tmp/' + str(uuid.uuid4())
        os.mkdir(dirname)
        return dirname

    def _extract_dirname_from_github_link(self):
        return self.github.rsplit('/', 2)[1] if self.github.endswith('/') else self.github.rsplit('/', 1)[1]

    def _clanup(self, location):
        shutil.rmtree(location)
