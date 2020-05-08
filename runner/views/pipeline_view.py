import json
from django.core.cache import cache
from rest_framework import status
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from runner.models import Pipeline
from runner.serializers import PipelineSerializer
from runner.serializers import PipelineResolvedSerializer
from runner.pipeline.pipeline_resolver import get_pipeline
from django.http import HttpResponse


class PipelineViewSet(mixins.ListModelMixin,
                      mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      GenericViewSet):
    queryset = Pipeline.objects.order_by('id').all()
    serializer_class = PipelineSerializer


class PipelineResolveViewSet(GenericAPIView):

    queryset = Pipeline.objects.order_by('id').all()
    serializer_class = PipelineResolvedSerializer

    def get(self, request, pk):
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            resolved_dict = get_pipeline(pipeline)
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
            resolved_dict = get_pipeline(pipeline)
        except Exception as e:
            return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(json.dumps(resolved_dict), content_type='text/plain; charset=UTF-8')
        response['Content-Disposition'] = ('attachment; filename={0}'.format('aplication.cwl'))
        return response
