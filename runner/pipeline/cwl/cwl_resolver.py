import uuid
import git
import os
import json
import subprocess
from django.conf import settings
from django.core.cache import cache
from runner.pipeline.pipeline_resolver import PipelineResolver


class CWLResolver(PipelineResolver):

    def __init__(self, github, entrypoint, version=None):
        super().__init__(github, entrypoint, version)

    def resolve(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        output_name = os.path.join(location, '%s.cwl' % str(uuid.uuid4()))
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

    def load(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        with open(os.path.join(location, self.entrypoint), 'r') as f:
            ret = json.load(f)
        self._cleanup(location)
        return ret


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
