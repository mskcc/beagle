import datetime
import logging
from distutils.util import strtobool
from functools import reduce

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from beagle.common import fix_query_list
from beagle.pagination import time_filter
from notifier.events import AddPipelineToDescriptionEvent, RunStartedEvent
from notifier.helper import generate_sample_data_content
from notifier.models import JobGroup, JobGroupNotifier
from notifier.tasks import notifier_start, send_notification
from runner.models import Operator, OperatorErrors, OperatorRun, Pipeline, Port, Run, RunStatus
from runner.operator.operator_factory import OperatorFactory
from runner.run.objects.run_creator_object import RunCreator
from runner.serializers import (
    AionOperatorSerializer,
    ArgosPairingSerializer,
    CWLJsonSerializer,
    OperatorErrorSerializer,
    OperatorLatestSamplesQuerySerializer,
    OperatorRunSerializer,
    OperatorSampleQuerySerializer,
    PairOperatorSerializer,
    RequestIdsOperatorSerializer,
    RestartRunSerializer,
    RunApiListSerializer,
    RunIdsOperatorSerializer,
    RunSamplesSerializer,
    RunSerializerCWLInput,
    RunSerializerCWLOutput,
    RunSerializerFull,
    RunSerializerPartial,
    TempoMPGenOperatorSerializer,
    TerminateRunSerializer,
)
from runner.tasks import (
    create_aion_job,
    create_jobs_from_operator,
    create_jobs_from_pairs,
    create_jobs_from_request,
    create_run_task,
    create_tempo_mpgen_job,
    run_routine_operator_job,
    submit_job,
    terminate_job_task,
)


def query_from_dict(query_filter, queryset, input_list):
    for single_input in input_list:
        key, val = single_input.split(":")
        query = {query_filter % key: val}
        queryset = queryset.filter(**query).all()
    return queryset


class RunApiViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = (
        Run.objects.prefetch_related(Prefetch("port_set", queryset=Port.objects.select_related("run")))
        .order_by("-created_date")
        .all()
    )

    def get_serializer_class(self):
        if self.action == "list":
            return RunApiListSerializer
        else:
            return RunSerializerFull

    @swagger_auto_schema(query_serializer=RunApiListSerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = [
            "job_groups",
            "request_ids",
            "inputs",
            "tags",
            "jira_ids",
            "run_ids",
            "apps",
            "run",
            "values_run",
            "ports",
            "sample_ids",
        ]
        fixed_query_params = fix_query_list(request.query_params, query_list_types)
        serializer = RunApiListSerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = time_filter(Run, fixed_query_params)
            job_groups = fixed_query_params.get("job_groups")
            jira_ids = fixed_query_params.get("jira_ids")
            run_ids = fixed_query_params.get("run_ids")
            status_param = fixed_query_params.get("status")
            ports = fixed_query_params.get("ports")
            tags = fixed_query_params.get("tags")
            operator_run = fixed_query_params.get("operator_run")
            request_ids = fixed_query_params.get("request_ids")
            sample_ids = fixed_query_params.get("sample_ids")
            apps = fixed_query_params.get("apps")
            values_run = fixed_query_params.get("values_run")
            run = fixed_query_params.get("run")
            run_distribution = fixed_query_params.get("run_distribution")
            count = fixed_query_params.get("count")
            full = fixed_query_params.get("full")
            if full:
                full = bool(strtobool(full))
            if operator_run:
                queryset = queryset.filter(operator_run_id=operator_run)
            if job_groups:
                queryset = queryset.filter(job_group__in=job_groups)
            if jira_ids:
                queryset = queryset.filter(job_group__jira_id__in=jira_ids)
            if run_ids:
                queryset = queryset.filter(id__in=run_ids)
            if status_param:
                queryset = queryset.filter(status=RunStatus[status_param].value)
            if ports:
                queryset = query_from_dict("port__%s__exact", queryset, ports)
            if tags:
                queryset = query_from_dict("tags__%s__contains", queryset, tags)
            if request_ids:
                queryset = queryset.filter(tags__igoRequestId__in=request_ids)
            if sample_ids:
                queryset = queryset.filter(samples__sample_id__in=sample_ids).distinct()
            if apps:
                queryset = queryset.filter(app__in=apps)
            if run:
                filter_query = dict()
                for single_run in run:
                    key, value = single_run.split(":")
                    if value == "True" or value == "true":
                        value = True
                    if value == "False" or value == "false":
                        value = False
                    filter_query[key] = value
                if filter_query:
                    queryset = queryset.filter(**filter_query)
            if values_run:
                if len(values_run) == 1:
                    ret_str = values_run[0]
                    queryset = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
                else:
                    values_run_query_list = [single_run for single_run in values_run]
                    values_run_query_set = set(values_run_query_list)
                    sorted_query_list = sorted(values_run_query_set)
                    queryset = queryset.values_list(*sorted_query_list).distinct()
            if run_distribution:
                distribution_dict = {}
                run_query = run_distribution
                run_ids = queryset.values_list("id", flat=True)
                queryset = Run.objects.all()
                queryset = queryset.filter(id__in=run_ids).values(run_query).order_by().annotate(Count(run_query))
                for single_arg in queryset:
                    single_arg_name = None
                    single_arg_count = 0
                    for single_key, single_value in single_arg.items():
                        if "count" in single_key:
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
        run_creator = RunCreator(**request.data)
        if run_creator.is_valid():
            run = run_creator.create()
            response = RunSerializerFull(run)
            create_run_task.delay(str(run.id), run_creator.inputs, run.output_directory)
            job_group_notifier_id = str(run.job_group_notifier_id)
            if job_group_notifier_id:
                self._send_notifications(job_group_notifier_id, run)
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response("Error", status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=TerminateRunSerializer)
    @action(detail=False, methods=["post"])
    def terminate(self, request, *args, **kwargs):
        serializer = TerminateRunSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        job_group_id = request.data.get("job_group_id", None)
        runs = request.data.get("runs", [])
        terminate_job_task.delay(job_group_id, runs)
        return Response("Terminate task submitted", status=status.HTTP_202_ACCEPTED)

    def _send_notifications(self, job_group_notifier_id, run):
        pipeline_name = run.app.name
        pipeline_version = run.app.version
        pipeline_link = run.app.pipeline_link

        pipeline_description_event = AddPipelineToDescriptionEvent(
            job_group_notifier_id, pipeline_name, pipeline_version, pipeline_link
        ).to_dict()
        send_notification.delay(pipeline_description_event)

        run_event = RunStartedEvent(
            job_group_notifier_id, str(run.id), run.app.name, run.app.pipeline_link, run.output_directory, run.tags
        ).to_dict()
        send_notification.delay(run_event)


class RunApiRestartViewSet(GenericAPIView):
    serializer_class = RestartRunSerializer

    logger = logging.getLogger(__name__)

    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        operator_run_id = serializer.validated_data.get("operator_run_id")
        clean = serializer.validated_data.get("clean")

        o = (
            OperatorRun.objects.select_related(
                "operator",
            )
            .prefetch_related("runs")
            .get(pk=operator_run_id)
        )
        if not o:
            return Response("Operator does not exist", status=status.HTTP_400_BAD_REQUEST)

        runs_in_progress = o.runs.exclude(status__in=[RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.TERMINATED])

        if runs_in_progress:
            job_group_id = runs_in_progress[0].job_group_id
            runs_in_progress_ids = list(runs_in_progress.values_list("id", flat=True))
            terminate_job_task.delay(job_group_id, runs_in_progress_ids)

        runs_to_restart = o.runs.exclude(status=RunStatus.COMPLETED)
        runs_to_restart.union(runs_in_progress)

        if not runs_to_restart:
            return Response("There are no runs to restart", status=status.HTTP_400_BAD_REQUEST)

        runs_to_copy_over = o.runs.filter(status=RunStatus.COMPLETED)

        o.pk = None
        o.status = RunStatus.RUNNING if len(runs_to_copy_over) > 0 else RunStatus.CREATING
        o.num_failed_runs = 0
        o.num_completed_runs = len(runs_to_copy_over)
        o.finished_date = None
        o.save()

        for r in runs_to_copy_over:
            ports = r.port_set.all()
            samples = r.samples.all()
            r.pk = None
            r.operator_run_id = o.pk
            r.save()
            r.samples.add(*samples)

            for p in ports:
                files = p.files.all()
                p.pk = None
                p.run_id = r.pk
                p.save()
                p.files.add(*files)

        for r in runs_to_restart:
            original_run_id = r.id
            ports = r.port_set.all()
            samples = r.samples.all()
            r.pk = None
            r.operator_run_id = o.pk
            r.reset_counters()
            r.clear().save()
            if clean == False:
                r.resume = original_run_id
            r.samples.add(*samples)

            r.save()

            for p in ports:
                files = p.files.all()
                p.pk = None
                p.run_id = r.pk
                p.save()
                p.files.add(*files)

            submit_job.delay(str(r.pk), r.output_directory)
            self._send_notifications(o.job_group_notifier_id, r)

        operator_run = OperatorRun.objects.get(id=operator_run_id)
        operator_run.increment_manual_restart()

        message = "This is restart number: {}, restarted {} runs and copied {} runs".format(
            operator_run.num_manual_restarts, str(len(runs_to_restart)), str(len(runs_to_copy_over))
        )

        return Response(
            message,
            status=status.HTTP_201_CREATED,
        )

    def _send_notifications(self, job_group_notifier_id, run):
        pipeline_name = run.app.name
        pipeline_version = run.app.version
        pipeline_link = run.app.pipeline_link

        pipeline_description_event = AddPipelineToDescriptionEvent(
            job_group_notifier_id, pipeline_name, pipeline_version, pipeline_link
        ).to_dict()
        send_notification.delay(pipeline_description_event)

        run_event = RunStartedEvent(
            job_group_notifier_id, str(run.id), run.app.name, run.app.pipeline_link, run.output_directory, run.tags
        ).to_dict()
        send_notification.delay(run_event)


class RequestOperatorViewSet(GenericAPIView):
    serializer_class = RequestIdsOperatorSerializer

    def post(self, request):
        request_ids = request.data.get("request_ids")
        pipeline_name = request.data.get("pipeline")
        pipeline_version = request.data.get("pipeline_version", None)
        job_group_id = request.data.get("job_group_id", None)
        file_group_id = request.data.get("file_group_id", None)
        for_each = request.data.get("for_each", True)

        if pipeline_version:
            pipeline = get_object_or_404(Pipeline, name=pipeline_name, version=pipeline_version)
        else:
            pipeline = get_object_or_404(Pipeline, name=pipeline_name, default=True)

        errors = []
        if not request_ids:
            errors.append("request_ids needs to be specified")
        if not pipeline:
            errors.append("pipeline needs to be specified")
        if errors:
            return Response({"details": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not job_group_id:
            if for_each:
                for req in request_ids:
                    job_group = JobGroup()
                    job_group.save()
                    job_group_id = str(job_group.id)
                    logging.info("Submitting requestId %s to pipeline %s" % (req, pipeline))
                    create_jobs_from_request.delay(
                        req, pipeline.operator_id, job_group_id, pipeline=str(pipeline.id), file_group=file_group_id
                    )
            else:
                return Response({"details": "Not Implemented"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if for_each:
                for req in request_ids:
                    logging.info("Submitting requestId %s to pipeline %s" % (req, pipeline))
                    try:
                        job_group_notifier = JobGroupNotifier.objects.get(
                            job_group_id=job_group_id, notifier_type_id=pipeline.operator.notifier_id
                        )
                        job_group_notifier_id = str(job_group_notifier.id)
                    except JobGroupNotifier.DoesNotExist:
                        job_group = JobGroup.objects.get(id=job_group_id)
                        job_group_notifier_id = notifier_start(job_group, req, pipeline.operator)
                    create_jobs_from_request.delay(
                        req,
                        pipeline.operator_id,
                        job_group_id,
                        job_group_notifier_id=job_group_notifier_id,
                        pipeline=str(pipeline.id),
                    )
            else:
                return Response({"details": "Not Implemented"}, status=status.HTTP_400_BAD_REQUEST)

        body = {"details": "Operator Job submitted %s" % str(request_ids)}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class RunOperatorViewSet(GenericAPIView):
    serializer_class = RunIdsOperatorSerializer

    def post(self, request):
        run_ids = request.data.get("run_ids")
        pipeline_names = request.data.get("pipelines")
        pipeline_versions = request.data.get("pipeline_versions", None)
        job_group_id = request.data.get("job_group_id", None)
        for_each = request.data.get("for_each", False)

        if not for_each:
            for i, pipeline_name in enumerate(pipeline_names):
                pipeline_version = pipeline_versions[i]
                get_object_or_404(Pipeline, name=pipeline_name, version=pipeline_version)
            try:
                run = Run.objects.get(id=run_ids[0])
                req = run.tags.get(settings.REQUEST_ID_METADATA_KEY, "Unknown")
            except Run.DoesNotExist:
                req = "Unknown"

            if not job_group_id:
                job_group = JobGroup()
                job_group.save()
                job_group_id = str(job_group.id)
                notifier_start(job_group, req)
            else:
                try:
                    job_group = JobGroup.objects.get(id=job_group_id)
                except JobGroup.DoesNotExist:
                    return Response(
                        {"details": "Invalid JobGroup: %s" % job_group_id}, status=status.HTTP_400_BAD_REQUEST
                    )

            for i, pipeline_name in enumerate(pipeline_names):
                pipeline_version = pipeline_versions[i]
                pipeline = get_object_or_404(Pipeline, name=pipeline_name, version=pipeline_version)
                try:
                    job_group_notifier = JobGroupNotifier.objects.get(
                        job_group_id=job_group_id, notifier_type_id=pipeline.operator.notifier_id
                    )
                    job_group_notifier_id = str(job_group_notifier.id)
                except JobGroupNotifier.DoesNotExist:
                    job_group_notifier_id = notifier_start(job_group, req, operator=pipeline.operator)

                operator_model = Operator.objects.get(id=pipeline.operator_id)
                operator = OperatorFactory.get_by_model(
                    operator_model,
                    run_ids=run_ids,
                    job_group_id=job_group_id,
                    job_group_notifier_id=job_group_notifier_id,
                    pipeline=str(pipeline.id),
                )
                create_jobs_from_operator(operator, job_group_id, job_group_notifier_id=job_group_notifier_id)
        else:
            return Response({"details": "Not Implemented"}, status=status.HTTP_400_BAD_REQUEST)

        body = {
            "details": "Operator Job submitted to pipelines %s, job group id %s,  with runs %s"
            % (pipeline_names, job_group_id, str(run_ids))
        }
        return Response(body, status=status.HTTP_202_ACCEPTED)


class PairsOperatorViewSet(GenericAPIView):
    serializer_class = PairOperatorSerializer

    def post(self, request):
        pairs = request.data.get("pairs")
        pipeline_names = request.data.get("pipelines")
        pipeline_versions = request.data.get("pipeline_versions")
        name = request.data.get("name")
        labHeadName = request.data.get("labHeadName")
        investigatorName = request.data.get("investigatorName")
        assay = request.data.get("assay")
        job_group_id = request.data.get("job_group_id", None)
        file_group_id = request.data.get("file_group_id", None)
        request_id = request.data.get("request_id", "missing_request_id")
        output_directory_prefix = request.data.get("output_directory_prefix", None)

        if not job_group_id:
            job_group = JobGroup()
            job_group.save()
            job_group_id = str(job_group.id)

        for i, pipeline_name in enumerate(pipeline_names):
            pipeline_version = pipeline_versions[i]
            pipeline = get_object_or_404(Pipeline, name=pipeline_name, version=pipeline_version)
            create_jobs_from_pairs.delay(
                str(pipeline.id),
                pairs,
                name,
                assay,
                investigatorName,
                labHeadName,
                file_group_id,
                job_group_id,
                request_id,
                output_directory_prefix,
            )

        body = {
            "details": "Operator Job submitted to pipelines %s, job group id %s, with pairs %s"
            % (pipeline_names, job_group_id, str(pairs))
        }
        return Response(body, status=status.HTTP_202_ACCEPTED)


class OperatorErrorViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = OperatorErrorSerializer
    queryset = OperatorErrors.objects.order_by("-created_date").all()


class CWLJsonViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)
    serializer_class = CWLJsonSerializer
    queryset = (
        Run.objects.prefetch_related(Prefetch("port_set", queryset=Port.objects.select_related("run")))
        .order_by("-created_date")
        .all()
    )

    @swagger_auto_schema(query_serializer=CWLJsonSerializer)
    def get(self, request):
        query_list_types = ["job_groups", "jira_ids", "request_ids", "runs"]
        fixed_query_params = fix_query_list(request.query_params, query_list_types)
        serializer = CWLJsonSerializer(data=fixed_query_params)
        show_inputs = False
        if serializer.is_valid():
            job_groups = fixed_query_params.get("job_groups")
            jira_ids = fixed_query_params.get("jira_ids")
            request_ids = fixed_query_params.get("request_ids")
            runs = fixed_query_params.get("runs")
            cwl_inputs = fixed_query_params.get("cwl_inputs")
            if not job_groups and not jira_ids and not request_ids and not runs:
                return Response("Error: No runs specified", status=status.HTTP_400_BAD_REQUEST)
            queryset = Run.objects.all()
            if job_groups:
                queryset = queryset.filter(job_group__in=job_groups)
            if jira_ids:
                queryset = queryset.filter(job_group_notifier__jira_id__in=jira_ids)
            if request_ids:
                queryset = queryset.filter(tags__igoRequestId__in=request_ids)
            if runs:
                queryset = queryset.filter(id__in=runs)
            if cwl_inputs:
                show_inputs = bool(strtobool(cwl_inputs))
            try:
                page = self.paginate_queryset(queryset.order_by("-created_date").all())
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
        lab_head_email = request.data.get("lab_head_email", [])
        if lab_head_email:
            operator_model = Operator.objects.get(class_name="AionOperator")
            operator = OperatorFactory.get_by_model(
                operator_model, job_group_id=job_group_id, job_group_notifier_id=job_group_notifier_id
            )
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
        normals_override = request.data.get("normals_override", [])
        tumors_override = request.data.get("tumors_override", [])
        operator_model = Operator.objects.get(slug="tempo_mpgen_operator")
        pairing_override = None
        heading = "TempoMPGen Run %s" % datetime.datetime.now().isoformat()
        job_group = JobGroup()
        job_group.save()
        job_group_id = str(job_group.id)
        job_group_notifier_id = notifier_start(job_group, heading, operator_model)
        operator = OperatorFactory.get_by_model(
            operator_model, job_group_id=job_group_id, job_group_notifier_id=job_group_notifier_id
        )
        if normals_override and tumors_override:
            pairing_override = dict()
            pairing_override["normal_samples"] = normals_override
            pairing_override["tumor_samples"] = tumors_override
            body = {"details": "Submitting TempoMPGen Job with pairing overrides."}
        else:
            body = {"details": "TempoMPGen Job submitted."}
        create_tempo_mpgen_job(operator, pairing_override, job_group_id, job_group_notifier_id)
        return Response(body, status=status.HTTP_202_ACCEPTED)


class ArgosPairingViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = ArgosPairingSerializer

    def post(self, request):
        igo_request_id = request.data.get("igo_request_id")
        argos_slug = request.data.get("argos_slug")
        operator_model = Operator.objects.get(slug=argos_slug)
        operator = OperatorFactory.get_by_model(operator_model, request_id=igo_request_id)
        # construct_argos_jobs() is sloppily separate from the Operator module
        from runner.operator.argos_operator.v2_2_1.construct_argos_pair import construct_argos_jobs

        files, cnt_tumors = operator.get_files(operator.request_id)
        data = operator.build_data_list(files)
        samples = operator.get_samples_from_data(data)
        argos_inputs, error_samples = construct_argos_jobs(samples)
        sample_pairing = operator.get_pairing_from_argos_inputs(argos_inputs)
        if sample_pairing:
            body = {"details": sample_pairing}
        else:
            message = "%s: No samples found." % igo_request_id
            body = {"details": message}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class ArgosMappingViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = ArgosPairingSerializer

    def post(self, request):
        igo_request_id = request.data.get("igo_request_id")
        argos_slug = request.data.get("argos_slug")
        operator_model = Operator.objects.get(slug=argos_slug)
        operator = OperatorFactory.get_by_model(operator_model, request_id=igo_request_id)
        # construct_argos_jobs() is sloppily separate from the Operator module
        from runner.operator.argos_operator.v2_2_1.construct_argos_pair import construct_argos_jobs

        files, cnt_tumors = operator.get_files(operator.request_id)
        data = operator.build_data_list(files)
        samples = operator.get_samples_from_data(data)
        argos_inputs, error_samples = construct_argos_jobs(samples)
        sample_mapping, filepaths = operator.get_mapping_from_argos_inputs(argos_inputs)
        if sample_mapping:
            body = {"details": sample_mapping}
        else:
            message = "%s: No samples found." % igo_request_id
            body = {"details": message}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class ArgosDataClinicalViewSet(GenericAPIView):
    logger = logging.getLogger(__name__)

    serializer_class = ArgosPairingSerializer

    def post(self, request):
        igo_request_id = request.data.get("igo_request_id")
        argos_slug = request.data.get("argos_slug")
        operator_model = Operator.objects.get(slug=argos_slug)
        operator = OperatorFactory.get_by_model(operator_model, request_id=igo_request_id)
        # construct_argos_jobs() and compile_pairs() are sloppily separate from the Operator module
        from runner.operator.argos_operator.v2_2_1.bin.pair_request import compile_pairs
        from runner.operator.argos_operator.v2_2_1.construct_argos_pair import construct_argos_jobs

        files, cnt_tumors = operator.get_files(operator.request_id)
        data = operator.build_data_list(files)
        samples = operator.get_samples_from_data(data)
        dmp_samples = list()
        for sample in samples:
            sample_type = sample["tumor_type"]
            this_sample, is_dmp_sample = operator.get_regular_sample(sample, sample_type)
            if is_dmp_sample:
                dmp_samples.append(this_sample)
        argos_inputs, error_samples = construct_argos_jobs(samples)
        sample_mapping, filepaths = operator.get_mapping_from_argos_inputs(argos_inputs)
        dmp_samples = operator.get_dmp_samples_from_argos_inputs(argos_inputs)
        pipeline = operator.get_pipeline_id()
        try:
            pipeline_obj = Pipeline.objects.get(id=pipeline)
        except Pipeline.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        data_clinical = generate_sample_data_content(
            filepaths,
            pipeline_name=pipeline_obj.name,
            pipeline_github=pipeline_obj.github,
            pipeline_version=pipeline_obj.version,
            dmp_samples=dmp_samples,
        )
        if data_clinical:
            body = {
                "details": data_clinical,
            }
        else:
            message = "%s: No samples found." % igo_request_id
            body = {"details": message}
        return Response(body, status=status.HTTP_202_ACCEPTED)


class RunSamplesViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = (
        Run.objects.prefetch_related(Prefetch("port_set", queryset=Port.objects.select_related("run")))
        .order_by("-created_date")
        .all()
    )

    def get_serializer_class(self):
        if self.action == "list":
            return RunApiListSerializer
        else:
            return RunSerializerFull

    @swagger_auto_schema(query_serializer=RunSamplesSerializer)
    def list(self, request, *args, **kwargs):
        job_group = request.query_params.get("job_group")
        samples = request.query_params.get("samples").split(",")
        results = Run.objects.filter(
            reduce(lambda x, y: x | y, [Q(samples__sample_id__contains=sample) for sample in samples])
        ).distinct()
        if job_group:
            results = results.filter(job_group=job_group)
        page = self.paginate_queryset(results)
        serializer = RunSerializerPartial(page, many=True)
        return self.get_paginated_response(serializer.data)


class OperatorSamplesLatestViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = OperatorRun.objects.all()
    serializer_class = OperatorRunSerializer

    @swagger_auto_schema(query_serializer=OperatorLatestSamplesQuerySerializer)
    def list(self, request, *args, **kwargs):
        samples = request.query_params.get("samples").split()
        response = dict()
        for sample in samples:
            latest_operator_run = (
                OperatorRun.objects.filter(
                    reduce(lambda x, y: x | y, [Q(runs__samples__sample_id__contains=sample) for sample in [sample]])
                )
                .order_by("-created_date")
                .first()
            )
            operator_runs = OperatorRun.objects.filter(job_group=latest_operator_run.job_group).all()
            serializer = OperatorRunSerializer(operator_runs, many=True)
            response[sample] = serializer.data
        return Response(response, status=status.HTTP_200_OK)


class OperatorSamplesAllViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = OperatorRun.objects.all()
    serializer_class = OperatorRunSerializer

    @swagger_auto_schema(query_serializer=OperatorSampleQuerySerializer)
    def list(self, request, *args, **kwargs):
        sample = request.query_params.get("sample")
        response = []
        operator_runs = OperatorRun.objects.filter(
            reduce(lambda x, y: x | y, [Q(runs__samples__sample_id__contains=sample) for sample in [sample]])
        ).order_by("-created_date")
        job_groups = [operator_run.job_group for operator_run in operator_runs]
        for job_group in job_groups:
            operators = OperatorRun.objects.filter(job_group=job_group)
            serializer = OperatorRunSerializer(operators, many=True)
            response.append(serializer.data)
        return Response(response, status=status.HTTP_200_OK)
