import json
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from runner.models import Pipeline
from runner.serializers import PipelineSerializer
from runner.serializers import PipelineResolvedSerializer
from runner.pipeline.pipeline_cache import PipelineCache
from django.http import HttpResponse


class PipelineViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      GenericViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer

    def get_queryset(self):
        queryset = self.queryset
        name = self.request.query_params.get('name', None)
        default = self.request.query_params.get('default', None)
        version = self.request.query_params.get('version', None)

        if name:
            queryset = queryset.filter(name=name)
        if default:
            queryset = queryset.filter(default=True)
        if version:
            queryset = queryset.filter(version=version)

        return queryset


class PipelineResolveViewSet(GenericAPIView):

    queryset = Pipeline.objects.order_by('id').all()
    serializer_class = PipelineResolvedSerializer

    def get(self, request, pk):
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            resolved_dict = PipelineCache.get_pipeline(pipeline)
        except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PipelineResolvedSerializer(data={'app': resolved_dict})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)


class PipelineDownloadViewSet(GenericAPIView):

    queryset = Pipeline.objects.order_by('id').all()
    serializer_class = PipelineSerializer

    def get(self, request, pk):
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            resolved_dict = PipelineCache.get_pipeline(pipeline)
        except Exception as e:
            return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(json.dumps(resolved_dict), content_type='text/plain; charset=UTF-8')
        response['Content-Disposition'] = ('attachment; filename={0}'.format('aplication.cwl'))
        return response
