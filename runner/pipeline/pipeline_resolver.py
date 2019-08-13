import uuid
import git
import os
import json
import shutil
import subprocess
from django.conf import settings


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
