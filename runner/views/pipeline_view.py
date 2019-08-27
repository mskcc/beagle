from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from runner.models import Pipeline
from runner.serializers import PipelineSerializer
from runner.serializers import PipelineResolvedSerializer
from runner.pipeline.pipeline_resolver import CWLResolver, Cache
from django.http import HttpResponse


pipeline_cache = Cache()


class PipelineViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      GenericViewSet):
    queryset = Pipeline.objects.order_by('id').all()
    serializer_class = PipelineSerializer


class PipelineResolveViewSet(GenericAPIView):

    def get(self, request, pk):
        global pipeline_cache
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        _pipeline = pipeline_cache.get(pk)
        if _pipeline and (_pipeline.get('github') == pipeline.github and
                          _pipeline.get('entrypoint') == pipeline.entrypoint and
                          _pipeline.get('version') == pipeline.version):
            resolved_dict = _pipeline.get('app')
        else:
            try:
                cwl_resolver = CWLResolver(pipeline.github, pipeline.entrypoint, pipeline.version)
                resolved_dict = cwl_resolver.resolve()
                pipeline_cache.put(pk, {'app': resolved_dict,
                                        'github': pipeline.github,
                                        'entrypoint': pipeline.entrypoint,
                                        'version': pipeline.version})
            except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PipelineResolvedSerializer(data={'app': resolved_dict})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)


class PipelineDownloadViewSet(GenericAPIView):

    def get(self, request, pk):
        global pipeline_cache
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        _pipeline = pipeline_cache.get(pk)
        if _pipeline and (_pipeline.get('github') == pipeline.github and
                          _pipeline.get('entrypoint') == pipeline.entrypoint and
                          _pipeline.get('version') == pipeline.version):
            resolved_dict = _pipeline.get('app')
        else:
            try:
                cwl_resolver = CWLResolver(pipeline.github, pipeline.entrypoint, pipeline.version)
                resolved_dict = cwl_resolver.resolve()
                pipeline_cache.put(pk, {'app': resolved_dict,
                                        'github': pipeline.github,
                                        'entrypoint': pipeline.entrypoint,
                                        'version': pipeline.version})
            except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PipelineResolvedSerializer(data={'app': resolved_dict})
        if serializer.is_valid():
            response = HttpResponse(serializer.data, content_type='text/plain; charset=UTF-8')
            response['Content-Disposition'] = ('attachment; filename={0}'.format('aplication.cwl'))
            return response
        return Response({}, status=status.HTTP_404_NOT_FOUND)

