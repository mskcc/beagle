import logging
from distutils.util import strtobool
from django.db.models import Count
from rest_framework import mixins
from rest_framework import status
from beagle.pagination import time_filter
from rest_framework.response import Response
from beagle_etl.jobs import TYPES
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from beagle_etl.models import JobStatus, Job, ETLConfiguration
from drf_yasg.utils import swagger_auto_schema
# from .jobs.lims_etl_jobs import create_request_job
from .serializers import JobSerializer, CreateJobSerializier, RequestIdLimsPullSerializer, JobQuerySerializer, AssaySerializer, AssayElementSerializer, AssayUpdateSerializer, JobsTypesSerializer
from beagle.common import fix_query_list


class JobViewSet(mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 GenericViewSet):
    queryset = Job.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return JobSerializer
        else:
            return CreateJobSerializier

    def create(self, request, *args, **kwargs):
        job_data = request.data
        serializer = CreateJobSerializier(data=job_data)
        if serializer.is_valid():
            job = serializer.save()
            response = JobSerializer(job)
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(query_serializer=JobQuerySerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = ['job_group','values_args','args']
        fixed_query_params = fix_query_list(request.query_params, query_list_types)
        serializer = JobQuerySerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = time_filter(Job, request.query_params)
            queryset = time_filter(Job, request.query_params,time_modal='modified_date', previous_queryset=queryset)
            job_group = fixed_query_params.get('job_group')
            job_type = fixed_query_params.get('type')
            sample_id = fixed_query_params.get('sample_id')
            request_id = fixed_query_params.get('request_id')
            st = fixed_query_params.get('status')
            values_args = fixed_query_params.get('values_args')
            args = fixed_query_params.get('args')
            args_distribution = fixed_query_params.get('args_distribution')
            count = fixed_query_params.get('count')
            if job_group:
                queryset = queryset.filter(job_group__in=job_group)
            if job_type:
                queryset = queryset.filter(run=TYPES[job_type])
            if sample_id:
                queryset = queryset.filter(args__sample_id=sample_id)
            if request_id:
                queryset = queryset.filter(args__request_id=request_id)
            if st:
                queryset = queryset.filter(status=JobStatus[st].value)
            if args:
                filter_query = dict()
                for single_arg in args:
                    key, value = single_arg.split(':')
                    key = 'args__%s' % key
                    if value == 'True' or value == 'true':
                        value = True
                    if value == 'False' or value == 'false':
                        value = False
                    filter_query[key] = value
                if filter_query:
                    queryset = queryset.filter(**filter_query)
            if values_args:
                if len(values_args) == 1:
                    ret_str = 'args__%s' % values_args[0]
                    queryset = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
                else:
                    values_args_query_list = ['args__%s' % single_arg for single_arg in values_args ]
                    values_args_query_set = set(values_args_query_list)
                    queryset = queryset.values_list(*values_args_query_set).order_by(values_args_query_list[0]).distinct()
            if args_distribution:
                distribution_dict = {}
                args_query = 'args__%s' % args_distribution
                job_ids = queryset.values_list('id',flat=True)
                queryset = Job.objects.all()
                queryset = queryset.filter(id__in=job_ids).values(args_query).order_by().annotate(Count(args_query))
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
            page = self.paginate_queryset(queryset.all())
            if page is not None:
                if values_args:
                    return self.get_paginated_response(page)
                else:
                    serializer = JobSerializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssayViewSet(GenericAPIView):
    serializer_class = AssaySerializer
    queryset = ETLConfiguration.objects.all()
    pagination_class = None

    @swagger_auto_schema(responses={200: AssayElementSerializer})
    def get(self, request):
        assay = ETLConfiguration.objects.first()
        if assay:
            assay_response = AssaySerializer(assay)
            return Response(assay_response.data, status=status.HTTP_200_OK)
        error_message_list = ["Assay list is empty"]
        return Response({'errors':error_message_list},status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AssayUpdateSerializer,responses={200: AssayElementSerializer})
    def post(self, request):
        request_data = dict(request.data)
        all_list = request_data.get('all')
        disabled_list = request_data.get('disabled')
        hold_list = request_data.get('hold')
        assay = ETLConfiguration.objects.first()
        error_message_list = []
        if assay:
            if all_list:
                assay.all_recipes = list(set(all_list))
            if disabled_list:
                assay.disabled_recipes = list(set(disabled_list))
            if hold_list:
                assay.hold_recipes = list(set(hold_list))
            for single_assay in assay.hold_recipes:
                if single_assay in assay.disabled_recipes:
                    error_message = "Assay {} is in both disabled and hold".format(single_assay)
                    error_message_list.append(error_message)
            combined_list = assay.hold_recipes + assay.disabled_recipes
            for single_assay in combined_list:
                if single_assay not in assay.all_recipes:
                    error_message = "Assay {} is not listed in all".format(single_assay)
                    error_message_list.append(error_message)
            if error_message_list:
                return Response({'errors':list(set(error_message_list))}, status=status.HTTP_400_BAD_REQUEST)
            assay.save()
            assay_response = AssaySerializer(assay)
            return Response(assay_response.data, status=status.HTTP_200_OK)
        error_message_list = ["Assay list is empty"]
        return Response({'errors':error_message_list}, status=status.HTTP_404_NOT_FOUND)


class RequestIdLimsPullViewSet(GenericAPIView):
    serializer_class = RequestIdLimsPullSerializer

    logger = logging.getLogger(__name__)

    def post(self, request):
        request_ids = request.data['request_ids']
        redelivery = request.data['redelivery']
        created_jobs = []
        # for request_id in request_ids:
            # job = create_request_job(request_id, redelivery)
            # created_jobs.append(job)
        return Response({"details": "Import requests from LIMS jobs submitted %s" % str(request_ids)},
                        status=status.HTTP_201_CREATED)


class GetJobsTypes(GenericAPIView):
    serializer_class = JobsTypesSerializer
    pagination_class = None
    queryset = Job.objects.none()

    def get(self, request):
        response_dict = { 'job_types': TYPES}
        return Response(response_dict, status=status.HTTP_200_OK)

