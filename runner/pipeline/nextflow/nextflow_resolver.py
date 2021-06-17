import os
import json
from runner.pipeline.pipeline_resolver import PipelineResolver


class NextflowResolver(PipelineResolver):

    def __init__(self, github, entrypoint, version=None):
        super().__init__(github, entrypoint, version)

    def resolve(self):
        dir = self._dir_name()
        location = self._git_clone(dir)
        with open(os.path.join(location, 'inputs.template.json'), 'r') as f:
            pipeline = json.loads(f)
        self._cleanup(location)
        return pipeline
