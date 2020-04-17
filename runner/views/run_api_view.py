import uuid
import logging
from django.shortcuts import get_object_or_404
from beagle.pagination import time_filter
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import mixins
from runner.tasks import create_run_task, create_jobs_from_operator, run_routine_operator_job
from runner.models import Run, Port, Pipeline, RunStatus, OperatorErrors, Operator
from runner.serializers import RunSerializerPartial, RunSerializerFull, APIRunCreateSerializer, \
    RequestIdOperatorSerializer, OperatorErrorSerializer
from rest_framework.generics import GenericAPIView
from runner.operator.operator_factory import OperatorFactory
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from runner.tasks import create_jobs_from_request


class RunApiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    serializer_class = RunSerializerFull

    def list(self, request, *args, **kwargs):
        queryset = time_filter(Run, request.query_params)
        job_group = request.query_params.getlist('job_group')
        if job_group:
            queryset = queryset.filter(job_group__in=job_group).all()
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
        request_ids = request.data.get('request_ids', [])
        run_ids = request.data.get('run_ids', [])
        job_group_id = request.data.get('job_group_id', [])
        pipeline_name = request.data['pipeline_name']
        pipeline = get_object_or_404(Pipeline, name=pipeline_name)

        if request_ids:
            for request_id in request_ids:
                logging.info("Submitting requestId %s to pipeline %s" % (request_id, pipeline_name))
                if job_group_id:
                    create_jobs_from_request.delay(request_id, pipeline.operator_id, job_group_id)
                else:
                    create_jobs_from_request.delay(request_id, pipeline.operator_id)
            body = {"details": "Operator Job submitted %s" % str(request_ids)}
        else:
            if run_ids:
                operator_model = Operator.objects.get(id=pipeline.operator_id)
                operator = OperatorFactory.get_by_model(operator_model, run_ids=run_ids)
                if job_group_id:
                    create_jobs_from_operator(operator, job_group_id)
                    body = {"details": "Operator Job submitted to pipeline %s, job group id %s,  with runs %s" % (pipeline_name, job_group_id,  str(run_ids))}
                else:
                    create_jobs_from_operator(operator)
                    body = {"details": "Operator Job submitted to pipeline %s with runs %s" % (pipeline_name, str(run_ids))}
            else:
                operator_model = Operator.objects.get(id=pipeline.operator_id)
                if job_group_id:
                    operator = OperatorFactory.get_by_model(operator_model, job_group_id=job_group_id)
                    run_routine_operator_job(operator, job_group_id)
                    body = {"details": "Operator Job submitted to operator %s (JobGroupId: %s)" % (operator, job_group_id)}
                else:
                    operator = OperatorFactory.get_by_model(operator_model)
                    run_routine_operator_job(operator)
                    body = {"details": "Operator Job submitted to operator %s" % operator}
        return Response(body, status=status.HTTP_200_OK)


class OperatorErrorViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           GenericViewSet):
    serializer_class = OperatorErrorSerializer
    queryset = OperatorErrors.objects.order_by('-created_date').all()
