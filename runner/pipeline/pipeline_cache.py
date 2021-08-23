from django.core.cache import cache
from runner.models import ProtocolType
from runner.pipeline.cwl.cwl_resolver import CWLResolver
from runner.pipeline.nextflow import NextflowResolver


class PipelineCache(object):

    @staticmethod
    def get_pipeline(pipeline):
        _pipeline = cache.get(pipeline.id)
        if _pipeline and (_pipeline.get('github') == pipeline.github and
                          _pipeline.get('entrypoint') == pipeline.entrypoint and
                          _pipeline.get('version') == pipeline.version):
            resolved_dict = _pipeline.get('app')
        else:
            resolver_class = PipelineCache._get_pipeline_resolver(pipeline.pipeline_type)
            resolver = resolver_class(pipeline.github,
                                      pipeline.entrypoint,
                                      pipeline.version)
            resolved_dict = resolver.resolve()
            cache.set(pipeline.id, {'app': resolved_dict,
                                    'github': pipeline.github,
                                    'entrypoint': pipeline.entrypoint,
                                    'version': pipeline.version})
        return resolved_dict

    @staticmethod
    def _get_pipeline_resolver(pipeline_type):
        if pipeline_type == ProtocolType.CWL:
            return CWLResolver
        elif pipeline_type == ProtocolType.NEXTFLOW:
            return NextflowResolver
