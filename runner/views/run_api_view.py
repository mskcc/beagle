import logging
from distutils.util import strtobool
import datetime
from django.shortcuts import get_object_or_404
from beagle.pagination import time_filter
from django.db import models
from django.db.models import Prefetch, Count
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework import mixins
from runner.tasks import create_run_task, create_jobs_from_operator, run_routine_operator_job
from runner.models import Run, Port, Pipeline, RunStatus, OperatorErrors, Operator
from runner.serializers import RunSerializerPartial, RunSerializerFull, APIRunCreateSerializer, \
    RequestIdOperatorSerializer, OperatorErrorSerializer, RunApiListSerializer, RequestIdsOperatorSerializer, \
    RunIdsOperatorSerializer, AionOperatorSerializer, RunSerializerCWLInput, RunSerializerCWLOutput, CWLJsonSerializer, \
    TempoMPGenOperatorSerializer
from rest_framework.generics import GenericAPIView
from runner.operator.operator_factory import OperatorFactory
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from runner.tasks import create_jobs_from_request, create_aion_job, create_tempo_mpgen_job
from file_system.repository import FileRepository
from notifier.models import JobGroup, JobGroupNotifier
from notifier.events import OperatorStartEvent, SetLabelEvent
from notifier.tasks import notifier_start
from notifier.tasks import send_notification
from drf_yasg.utils import swagger_auto_schema
from beagle.common import fix_query_list


class RunApiViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return RunApiListSerializer
        else:
            return RunSerializerFull

    def query_from_dict(self,query_filter,queryset,input_list):
        for single_input in input_list:
            key, val = single_input.split(':')
            query = {query_filter % key: val}
            queryset = queryset.filter(**query).all()
        return queryset

    @swagger_auto_schema(query_serializer=RunApiListSerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = ['job_groups','request_ids','inputs','tags','jira_ids','apps','run','values_run','ports']
        fixed_query_params = fix_query_list(request.query_params,query_list_types)
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
            apps = fixed_query_params.get('apps')
            values_run = fixed_query_params.get('values_run')
            run = fixed_query_params.get('run')
            run_distribution = fixed_query_params.get('run_distribution')
            count = fixed_query_params.get('count')
            full = fixed_query_params.get('full')
            if full:
                full = bool(strtobool(full))
            if job_groups:
                queryset = queryset.filter(job_group__in=job_groups)
            if jira_ids:
                queryset = queryset.filter(job_group__jira_id__in=jira_ids)
            if status_param:
                queryset = queryset.filter(status=RunStatus[status_param].value)
            if ports:
                queryset = self.query_from_dict("port__%s__exact",queryset,ports)
            if tags:
                queryset = self.query_from_dict("tags__%s__exact",queryset,tags)
            if request_ids:
                queryset = queryset.filter(tags__requestId__in=request_ids)
            if apps:
                queryset = queryset.filter(app__in=apps)
            if run:
                filter_query = dict()
                for single_run in run:
                    key, value = single_run.split(':')
                    if value == 'True' or value == 'true':
                        value = True
                    if value == 'False' or value == 'false':
                        value = False
                    filter_query[key] = value
                if filter_query:
                    queryset = queryset.filter(**filter_query)
            if values_run:
                if len(values_run) == 1:
                    ret_str = values_run[0]
                    queryset = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
                else:
                    values_run_query_list = [single_run for single_run in values_run ]
                    values_run_query_set = set(values_run_query_list)
                    queryset = queryset.values_list(*values_run_query_set).distinct()
            if run_distribution:
                distribution_dict = {}
                run_query = run_distribution
                run_ids = queryset.values_list('id',flat=True)
                queryset = Run.objects.all()
                queryset = queryset.filter(id__in=run_ids).values(run_query).order_by().annotate(Count(run_query))
                for single_arg in queryset:
                    single_arg_name = None
                    single_arg_count = 0
                    for single_key, single_value in single_arg.items():
                        if 'count' in single_key:
                            single_arg_count = single_value
                        else:
                            single_arg_name = single_value
                    if single_arg_name is not None:
                        distribution_dict[single_arg_name] = single_arg_count
                return Response(distribution_dict, status=status.HTTP_200_OK)
            if count:
                count = bool(strtobool(count))
                if count:
                    return Response(queryset.count(), status=status.HTTP_200_OK)
            try:
                page = self.paginate_queryset(queryset.all())
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            if page is not None:
                if values_run:
                    return self.get_paginated_response(page)
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
                if not job_group_id:
                    job_group = JobGroup.objects.create()
                    job_group_id = str(job_group.id)
                create_jobs_from_request.delay(request_id, pipeline.operator_id, job_group_id)
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


class RequestOperatorViewSet(GenericAPIView):
    serializer_class = RequestIdsOperatorSerializer

    def post(self, request):
        request_ids = request.data.get('request_ids')
        pipeline_name = request.data.get('pipeline')
        job_group_id = request.data.get('job_group_id', None)
        for_each = request.data.get('for_each', True)

        pipeline = get_object_or_404(Pipeline, name=pipeline_name)

        errors = []
        if not request_ids:
            errors.append('request_ids needs to be specified')
        if not pipeline:
            errors.append('pipeline needs to be specified')
        if errors:
            return Response({'details': errors}, status=status.HTTP_400_BAD_REQUEST)

        if not job_group_id:
            if for_each:
                for req in request_ids:
                    job_group = JobGroup()
                    job_group.save()
                    job_group_id = str(job_group.id)
                    logging.info("Submitting requestId %s to pipeline %s" % (req, pipeline))
                    create_jobs_from_request.delay(req,
                                                   pipeline.operator_id,
                                                   job_group_id,
                                                   pipeline=str(pipeline.id))
            else:
                return Response({'details': 'Not Implemented'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if for_each:
                for req in request_ids:
                    logging.info("Submitting requestId %s to pipeline %s" % (req, pipeline))
                    try:
                        job_group_notifier = JobGroupNotifier.objects.get(job_group_id=job_group_id,
                                                                          notifier_type_id=pipeline.operator.notifier_id)
                        job_group_notifier_id = str(job_group_notifier.id)
                    except JobGroupNotifier.DoesNotExist:
                        job_group_notifier_id = notifier_start(job_group_id, req, pipeline.operator)
                    create_jobs_from_request.delay(req, pipeline.operator_id,
                                                   job_group_id,
                                                   job_group_notifier_id=job_group_notifier_id,
                                                   pipeline=str(pipeline.id))
            else:
                return Response({'details': 'Not Implemented'}, status=status.HTTP_400_BAD_REQUEST)

        body = {"details": "Operator Job submitted %s" % str(request_ids)}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class RunOperatorViewSet(GenericAPIView):
    serializer_class = RunIdsOperatorSerializer

    def post(self, request):
        run_ids = request.data.get('run_ids')
        pipeline_names = request.data.get('pipelines')
        job_group_id = request.data.get('job_group_id', None)
        for_each = request.data.get('for_each', False)

        if not for_each:
            for pipeline_name in pipeline_names:
                get_object_or_404(Pipeline, name=pipeline_name)

            try:
                run = Run.objects.get(id=run_ids[0])
                req = run.tags.get('requestId', 'Unknown')
            except Run.DoesNotExist:
                req = 'Unknown'

            if not job_group_id:
                job_group = JobGroup()
                job_group.save()
                job_group_id = str(job_group.id)
                notifier_start(job_group, req)
            else:
                try:
                    job_group = JobGroup.objects.get(id=job_group_id)
                except JobGroup.DoesNotExist:
                    return Response({'details': 'Invalid JobGroup: %s' % job_group_id},
                                    status=status.HTTP_400_BAD_REQUEST)

            for pipeline_name in pipeline_names:
                pipeline = get_object_or_404(Pipeline, name=pipeline_name)
                try:
                    job_group_notifier = JobGroupNotifier.objects.get(job_group_id=job_group_id,
                                                                      notifier_type_id=pipeline.operator.notifier_id)
                    job_group_notifier_id = str(job_group_notifier.id)
                except JobGroupNotifier.DoesNotExist:
                    job_group_notifier_id = notifier_start(job_group, req)

                operator_model = Operator.objects.get(id=pipeline.operator_id)
                operator = OperatorFactory.get_by_model(operator_model, run_ids=run_ids, job_group_id=job_group_id,
                                                        job_group_notifier_id=job_group_notifier_id)
                create_jobs_from_operator(operator, job_group_id, job_group_notifier_id=job_group_notifier_id)
        else:
            return Response({'details': 'Not Implemented'}, status=status.HTTP_400_BAD_REQUEST)

        body = {"details": "Operator Job submitted to pipelines %s, job group id %s,  with runs %s" % (
            pipeline_names, job_group_id, str(run_ids))}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class OperatorErrorViewSet(mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           GenericViewSet):
    serializer_class = OperatorErrorSerializer
    queryset = OperatorErrors.objects.order_by('-created_date').all()


class CWLJsonViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)
    serializer_class = CWLJsonSerializer
    queryset = Run.objects.prefetch_related(Prefetch('port_set', queryset=
    Port.objects.select_related('run'))).order_by('-created_date').all()

    @swagger_auto_schema(query_serializer=CWLJsonSerializer)
    def get(self, request):
        query_list_types = ['job_groups','jira_ids','request_ids','runs']
        fixed_query_params = fix_query_list(request.query_params,query_list_types)
        serializer = CWLJsonSerializer(data=fixed_query_params)
        show_inputs = False
        if serializer.is_valid():
            job_groups = fixed_query_params.get('job_groups')
            jira_ids = fixed_query_params.get('jira_ids')
            request_ids = fixed_query_params.get('request_ids')
            runs = fixed_query_params.get('runs')
            cwl_inputs = fixed_query_params.get('cwl_inputs')
            if not job_groups and not jira_ids and not request_ids and not runs:
                return Response("Error: No runs specified", status=status.HTTP_400_BAD_REQUEST)
            queryset = Run.objects.all()
            if job_groups:
                queryset = queryset.filter(job_group__in=job_groups)
            if jira_ids:
                queryset = queryset.filter(job_group__jira_id__in=jira_ids)
            if request_ids:
                queryset = queryset.filter(tags__requestId__in=request_ids)
            if runs:
                queryset = queryset.filter(id__in=runs)
            if cwl_inputs:
                show_inputs = bool(strtobool(cwl_inputs))
            try:
                page = self.paginate_queryset(queryset.order_by('-created_date').all())
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            if page is not None:
                if show_inputs:
                    serializer = RunSerializerCWLInput(page, many=True)
                else:
                    serializer = RunSerializerCWLOutput(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                return Response([], status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AionViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = AionOperatorSerializer

    def post(self, request):
        lab_head_email = request.data.get('lab_head_email', [])
        if lab_head_email:
            operator_model = Operator.objects.get(class_name="AionOperator")
            operator = OperatorFactory.get_by_model(operator_model, job_group_id=job_group_id,
                                                    job_group_notifier_id=job_group_notifier_id)
            heading = "Aion Run for %s" % lab_head_email
            job_group = JobGroup()
            job_group.save()
            job_group_id = str(job_group.id)
            job_group_notifier_id = notifier_start(job_group, heading, operator_model)
            create_aion_job(operator, lab_head_email, job_group_id, job_group_notifier_id)
            body = {"details": "Aion Job submitted for %s" % lab_head_email}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class TempoMPGenViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = TempoMPGenOperatorSerializer

    def post(self, request):
        normals_override = request.data.get('normals_override', [])
        tumors_override = request.data.get('tumors_override', [])
        operator_model = Operator.objects.get(slug="tempo_mpgen_operator")
        pairing_override=None
        heading = "TempoMPGen Run %s" % datetime.datetime.now().isoformat()
        job_group = JobGroup()
        job_group.save()
        job_group_id = str(job_group.id)
        job_group_notifier_id = notifier_start(job_group, heading, operator_model)
        operator = OperatorFactory.get_by_model(operator_model, job_group_id=job_group_id,
                                                job_group_notifier_id=job_group_notifier_id)
        if normals_override and tumors_override:
            pairing_override = dict()
            pairing_override['normal_samples'] = normals_override
            pairing_override['tumor_samples'] = tumors_override
            body = {"details": "Submitting TempoMPGen Job with pairing overrides."}
        else:
            body = {"details": "TempoMPGen Job submitted."}
        create_tempo_mpgen_job(operator, pairing_override, job_group_id, job_group_notifier_id)
        return Response(body, status=status.HTTP_202_ACCEPTED)
