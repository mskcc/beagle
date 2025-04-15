import json
import uuid
import base64
import requests
from beagle.pagination import time_filter
from django.conf import settings
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import mixins
from runner.models import Run, Port, RunStatus
from runner.serializers import RunSerializerFull, CreateRunSerializer, UpdateRunSerializer, RunStatusUpdateSerializer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import GenericAPIView
from runner.pipeline.pipeline_cache import PipelineCache


class RunViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = (
        Run.objects.prefetch_related(Prefetch("port_set", queryset=Port.objects.select_related("run")))
        .order_by("-created_date")
        .all()
    )

    def get_serializer_class(self):
        if self.action == "list" or self.action == "retrieve":
            return RunSerializerFull
        if self.action == "update":
            return UpdateRunSerializer
        return CreateRunSerializer

    def list(self, request, *args, **kwargs):
        queryset = time_filter(Run, request.query_params)
        status_param = request.query_params.get("status")
        if status_param:
            if status_param not in [s.name for s in RunStatus]:
                return Response(
                    {
                        "details": "Invalid status value %s: expected values %s"
                        % (status_param, [s.name for s in Status])
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=RunStatus[status_param].value)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RunSerializerFull(page, many=True)
            return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CreateRunSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            run = serializer.save()
            response = RunSerializerFull(run)
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateJob(GenericAPIView):

    queryset = Run.objects.all()
    serializer_class = RunStatusUpdateSerializer

    def post(self, request, pk):
        try:
            run = Run.objects.get(execution_id=pk)
        except Run.DoesNotExist:
            return Response({"details": "Couldn't find the job %s" % str(pk)}, status=status.HTTP_404_NOT_FOUND)
        serializer = RunStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
