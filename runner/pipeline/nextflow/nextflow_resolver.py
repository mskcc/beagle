import os
import git
import uuid
from runner.pipeline.pipeline_resolver import PipelineResolver


class NextflowResolver(PipelineResolver):

    def __init__(self, github, entrypoint, version=None):
        super().__init__(github, entrypoint, version)
