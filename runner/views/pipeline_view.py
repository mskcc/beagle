from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from runner.models import Pipeline
from runner.serializers import PipelineSerializer
from runner.pipeline.pipeline_resolver import CWLResolver


class PipelineViewSet(GenericAPIView):

    def get(self, request, pk):
        try:
            pipeline = Pipeline.objects.get(id=pk)
            cwl_resolver = CWLResolver(pipeline.github, pipeline.entrypoint, pipeline.version)
            resolved_dict = cwl_resolver.resolve()
        except Exception as e:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PipelineSerializer(data={'app': resolved_dict})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)
