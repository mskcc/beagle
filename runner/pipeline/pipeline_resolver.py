import os
import git
import uuid
import shutil


class PipelineResolver(object):

    def __init__(self, github, entrypoint, version=None):
        self.github = github
        self.entrypoint = entrypoint
        self.version = version

    def _git_clone(self, location):
        git.Git(location).clone(self.github, '--branch', self.version, '--recurse-submodules')
        dirname = self._extract_dirname_from_github_link()
        return os.path.join(location, dirname)

    def _dir_name(self):
        dirname = '/tmp/' + str(uuid.uuid4())
        os.mkdir(dirname)
        return dirname

    def _extract_dirname_from_github_link(self):
        dirname = self.github.rsplit('/', 2)[1] if self.github.endswith('/') else self.github.rsplit('/', 1)[1]
        if dirname.endswith('.git'):
            dirname = dirname[:-4]
        return dirname

    def _cleanup(self, location):
        shutil.rmtree(location)

    def load(self):
        pass

    def resolve(self):
        pass
