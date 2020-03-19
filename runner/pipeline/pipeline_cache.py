from django.core.cache import cache
from runner.pipeline.pipeline_resolver import CWLResolver


class PipelineCache(object):

    @staticmethod
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
