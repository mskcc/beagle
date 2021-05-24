from django.core.cache import cache
from runner.models import RunType
from runner.pipeline.cwl.cwl_resolver import CWLResolver
from runner.pipeline.nextflow import NextflowResolver


class PipelineCache(object):

    @staticmethod
    def get_pipeline(pipeline, pipeline_type):
        _pipeline = cache.get(pipeline.id)
        if _pipeline and (_pipeline.get('github') == pipeline.github and
                          _pipeline.get('entrypoint') == pipeline.entrypoint and
                          _pipeline.get('version') == pipeline.version):
            resolved_dict = _pipeline.get('app')
        else:
            if pipeline_type == RunType.CWL:
                cwl_resolver = CWLResolver(pipeline.github, pipeline.entrypoint, pipeline.version)
                resolved_dict = cwl_resolver.resolve()
                cache.set(pipeline.id, {'app': resolved_dict,
                                        'github': pipeline.github,
                                        'entrypoint': pipeline.entrypoint,
                                        'version': pipeline.version})
            elif pipeline_type == RunType.NEXTFLOW:
                nextflow_resolver = NextflowResolver(pipeline.github, pipeline.entrypoint, pipeline.version)

        return resolved_dict
