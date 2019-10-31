import json
import uuid
import base64
import requests
from django.conf import settings
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import mixins
from runner.tasks import create_run_task
from runner.models import Run, Port, Pipeline, RunStatus
from runner.serializers import RunSerializer, APIRunCreateSerializer, UpdateRunSerializer, RunStatusUpdateSerializer, TempoOperatorTestSerializer
from runner.operator.tempo_operator.tempo_operator import TempoOperator
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class RunApiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    serializer_class = RunSerializer

    def create(self, request, *args, **kwargs):
        serializer = APIRunCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            run = serializer.save()
            response = RunSerializer(run)
            create_run_task.delay(run.id, request.data['inputs'])
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TempoOperatorViewSet(GenericAPIView):
    serializer_class = TempoOperatorTestSerializer

    def post(self, request):
        request_id = request.data['request_id']
        tempo_operator = TempoOperator(request_id)
        jobs = tempo_operator.get_jobs()
        result = []
        for job in jobs:
            if job.is_valid():
                run = job.save()
                result.append(run)
        response = RunSerializer(result, many=True)
        return Response(response.data, status=status.HTTP_200_OK)
