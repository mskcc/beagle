import uuid
import git
import os
import json
import yaml
import shutil
import subprocess
from django.conf import settings
from django.core.cache import cache


class CWLResolver(object):

    def __init__(self, github, entrypoint, version=None):
        self.github = github
        self.entrypoint = entrypoint
        self.version = version

    def resolve(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        output_name = os.path.join(location, '%s.cwl' % str(uuid.uuid4()))
        print(settings.RABIX_PATH)
        print(location)
        print(self.entrypoint)
        with open(output_name, 'w') as out:
            subprocess.check_call([settings.RABIX_PATH, '-r', os.path.join(location, self.entrypoint)], stdout=out)
        with open(output_name) as f:
            pipeline = json.load(f)
        self._cleanup(location)
        return pipeline

    def create_file(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        output_name = os.path.join(location, '%s.cwl' % str(uuid.uuid4()))
        with open(output_name, 'w') as out:
            subprocess.check_call([settings.RABIX_PATH, '-r', os.path.join(location, self.entrypoint)], stdout=out)
        return output_name

    def _git_clone(self, location):
        git.Git(location).clone(self.github, '--branch', self.version, '--recurse-submodules')
        dirname = self._extract_dirname_from_github_link()
        return os.path.join(location, dirname)

    def load(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        with open(os.path.join(location, self.entrypoint), 'r') as f:
            try:
                ret = yaml.load(f)
            except Exception:
                ret = json.load(f)
        self._cleanup(location)
        return ret

    def _dir_name(self):
        dirname = '/tmp/' + str(uuid.uuid4())
        os.mkdir(dirname)
        return dirname

    def _extract_dirname_from_github_link(self):
        return self.github.rsplit('/', 2)[1] if self.github.endswith('/') else self.github.rsplit('/', 1)[1]

    def _cleanup(self, location):
        shutil.rmtree(location)


def get_pipeline(pipeline):
    _pipeline = cache.get(pipeline.id)
    if _pipeline and (_pipeline.get('github') == pipeline.github and
                      _pipeline.get('entrypoint') == pipeline.entrypoint and
                      _pipeline.get('version') == pipeline.version):
        resolved_dict = _pipeline.get('app')
    else:
        cwl_resolver = CWLResolver(pipeline.github, pipeline.entrypoint, pipeline.version)
        resolved_dict = cwl_resolver.resolve()
        cache.set(pipeline.id, {'app': resolved_dict,
                                'github': pipeline.github,
                                'entrypoint': pipeline.entrypoint,
                                'version': pipeline.version})
    return resolved_dict
