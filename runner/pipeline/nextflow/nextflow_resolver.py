import os
import git
import uuid
import glob
from runner.pipeline.pipeline_resolver import PipelineResolver


class NextflowResolver(PipelineResolver):

    def __init__(self, github, entrypoint, version=None):
        super().__init__(github, entrypoint, version)

    def resolve(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        inputs = glob.glob(os.path.join(location, '*.template'))
        for input in inputs:
            pass
