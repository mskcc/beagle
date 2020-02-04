import json
import uuid
import base64
import requests
import logging
from django.conf import settings
from beagle.pagination import time_filter
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import mixins
from runner.tasks import create_run_task, operator_job
from runner.models import Run, Port, Pipeline, RunStatus, OperatorErrors
from runner.serializers import RunSerializerPartial, RunSerializerFull, APIRunCreateSerializer, RequestIdOperatorSerializer, OperatorErrorSerializer
from runner.operator.tempo_operator.tempo_operator import TempoOperator
from rest_framework.generics import GenericAPIView
from runner.pipeline.pipeline_resolver import CWLResolver
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class RunApiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    serializer_class = RunSerializerFull

    def list(self, request, *args, **kwargs):

        queryset = Run.objects.prefetch_related(
            Prefetch('port_set', queryset=Port.objects.select_related('run'))).order_by('-created_date').all()
        queryset = time_filter(Run, request.query_params)
        status_param = request.query_params.get('status')
        if status_param:
            if status_param not in [s.name for s in RunStatus]:
                return Response({'details': 'Invalid status value %s: expected values %s' % (status_param, [s.name for s in RunStatus])}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(status=RunStatus[status_param].value)
        input_params = request.query_params.get('input')
        if input_params:
            inputs = input_params.split(',')
            for input in inputs:
                try:
                    key, val = input.split(':')
                    query = {"port__value__%s" % key: val}
                    queryset = queryset.filter(**query).all()
                except Exception as e:
                    return Response({'details': 'Query for inputs needs to be in format input:value'},
                                    status=status.HTTP_400_BAD_REQUEST)
        request_id = request.query_params.get('requestId')
        if request_id:
            queryset = queryset.filter(tags__requestId=request_id).all()
        page = self.paginate_queryset(queryset)
        full = request.query_params.get('full')
        if page is not None:
            if full:
                serializer = RunSerializerFull(page, many=True)
            else:
                serializer = RunSerializerPartial(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response([], status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        serializer = APIRunCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            run = serializer.save()
            response = RunSerializerFull(run)
            # cwl_resolver = CWLResolver(run.app.github, run.app.entrypoint, run.app.version)
            # resolved_dict = cwl_resolver.resolve()
            # task = runner.run.run_creator.Run(resolved_dict, request.data['inputs'])
            # for input in task.inputs:
            #     port = Port(run=run, name=input.id, port_type=input.type, schema=input.schema,
            #                 secondary_files=input.secondary_files, db_value=request.data['inputs'][input.id], value=input.value)
            #     port.save()
            # for output in task.outputs:
            #     port = Port(run=run, name=output.id, port_type=output.type, schema=output.schema,
            #                 secondary_files=output.secondary_files, db_value=output.value)
            #     port.save()
            create_run_task.delay(response.data['id'], request.data['inputs'])
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OperatorViewSet(GenericAPIView):
    serializer_class = RequestIdOperatorSerializer

    logger = logging.getLogger(__name__)

    def post(self, request):
        request_ids = request.data['request_ids']
        pipeline_name = request.data['pipeline_name']
        for request_id in request_ids:
            logging.info("Submitting requestId %s to pipeline %s" % (request_id, pipeline_name))
            operator_job.delay(request_id, pipeline_name)
        # tempo_operator = TempoOperator(request_id)
        # jobs = tempo_operator.get_jobs()
        # result = []
        # for job in jobs:
        #     if job.is_valid():
        #         run = job.save()
        #         result.append(run)
        return Response({"details": "Operator Job submitted %s" % str(request_ids)}, status=status.HTTP_200_OK)


class OperatorErrorViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           GenericViewSet):
    serializer_class = OperatorErrorSerializer
    queryset = OperatorErrors.objects.order_by('-created_date').all()
