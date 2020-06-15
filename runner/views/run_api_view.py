import uuid
import logging
from django.shortcuts import get_object_or_404
from beagle.pagination import time_filter
from django.db.models import Prefetch
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework import mixins
from runner.tasks import create_run_task, create_jobs_from_operator, run_routine_operator_job
from runner.models import Run, Port, Pipeline, RunStatus, OperatorErrors, Operator
from runner.serializers import RunSerializerPartial, RunSerializerFull, APIRunCreateSerializer, \
    RequestIdOperatorSerializer, OperatorErrorSerializer, RunApiListSerializer
from rest_framework.generics import GenericAPIView
from runner.operator.operator_factory import OperatorFactory
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from runner.tasks import create_jobs_from_request
from drf_yasg.utils import swagger_auto_schema


class RunApiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return RunApiListSerializer
        else:
            return RunSerializerFull

    def fix_query_list(self,request_query,key_list):
        query_dict = request_query.dict()
        for single_param in key_list:
            query_value = request_query.getlist(single_param)
            if query_value:
                if ',' in query_value[0]:
                    query_value = query_dict.get(single_param)
                    query_dict[single_param] = query_value.split(",")
                else:
                    query_dict[single_param] = query_value
        return query_dict

    def query_from_dict(self,query_filter,queryset,input_list):
        for single_input in input_list:
            key, val = single_input.split(':')
            query = {query_filter % key: val}
            queryset = queryset.filter(**query).all()
        return queryset

    @swagger_auto_schema(query_serializer=RunApiListSerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = ['job_groups','request_ids','inputs','tags','jira_ids']
        fixed_query_params = self.fix_query_list(request.query_params,query_list_types)
        serializer = RunApiListSerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = time_filter(Run, fixed_query_params)
            queryset = time_filter(Run, request.query_params,time_modal='modified_date', previous_queryset=queryset)
            job_groups = fixed_query_params.get('job_groups')
            jira_ids = fixed_query_params.get('jira_ids')
            status_param = fixed_query_params.get('status')
            ports = fixed_query_params.get('ports')
            tags = fixed_query_params.get('tags')
            request_ids = fixed_query_params.get('request_ids')
            if job_groups:
                queryset = queryset.filter(job_group__in=job_groups).all()
            if jira_ids:
                queryset = queryset.filter(job_group__jira_id__in=jira_ids).all()
            if status_param:
                queryset = queryset.filter(status=RunStatus[status_param].value).all()
            if ports:
                queryset = self.query_from_dict("port__value__%s",queryset,ports)
            if tags:
                queryset = self.query_from_dict("tags__%s__exact",queryset,tags)
            if request_ids:
                queryset = queryset.filter(tags__requestId__in=request_ids).all()
            try:
                page = self.paginate_queryset(queryset)
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            full = fixed_query_params.get('full')
            if page is not None:
                if full:
                    serializer = RunSerializerFull(page, many=True)
                else:
                    serializer = RunSerializerPartial(page, many=True)
                return self.get_paginated_response(serializer.data)
            return Response([], status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                if job_group_id:
                    operator = OperatorFactory.get_by_model(operator_model, run_ids=run_ids, job_group_id=job_group_id)
                    create_jobs_from_operator(operator, job_group_id)
                    body = {"details": "Operator Job submitted to pipeline %s, job group id %s,  with runs %s" % (pipeline_name, job_group_id,  str(run_ids))}
                else:
                    operator = OperatorFactory.get_by_model(operator_model, run_ids=run_ids)
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
