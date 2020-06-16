import logging
from rest_framework import mixins
from rest_framework import status
from beagle.pagination import time_filter
from rest_framework.response import Response
from beagle_etl.jobs import TYPES
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from beagle_etl.models import JobStatus, Job, Assay
from drf_yasg.utils import swagger_auto_schema
from .jobs.lims_etl_jobs import get_or_create_request_job
from .serializers import JobSerializer, CreateJobSerializier, RequestIdLimsPullSerializer, JobQuerySerializer, AssaySerializer, AssayElementSerializer, AssayUpdateSerializer
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
        query_list_types = ['job_group', 'type', 'sample_id', 'request_id']
        fixed_query_params = self.fix_query_list(request.query_params, query_list_types)
        serializer = JobQuerySerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = time_filter(Job, request.query_params)
            queryset = time_filter(Job, request.query_params,time_modal='modified_date', previous_queryset=queryset)
            job_group = fixed_query_params.get('job_group')
            if job_group:
                queryset = queryset.filter(job_group__in=job_group).all()
            job_type = fixed_query_params.get('type')
            if job_type:
                queryset = queryset.filter(run=TYPES[job_type])
            sample_id = fixed_query_params.get('sample_id')
            if sample_id:
                queryset = queryset.filter(args__sample_id=sample_id)
            request_id = fixed_query_params.get('request_id')
            if request_id:
                queryset = queryset.filter(args__request_id=request_id)
            st = fixed_query_params.get('status')
            if st:
                queryset = queryset.filter(status=JobStatus[st].value)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = JobSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def fix_query_list(self, request_query, key_list):
        query_dict = request_query.dict()
        for single_param in key_list:
            query_value = request_query.get(single_param)
            if query_value:
                if ',' in query_value[0]:
                    query_value = query_dict.get(single_param)
                    query_dict[single_param] = query_value.split(",")
                else:
                    query_dict[single_param] = query_value
        return query_dict


class AssayViewSet(GenericAPIView):
    serializer_class = AssaySerializer
    queryset = Assay.objects.all()
    pagination_class = None

    @swagger_auto_schema(responses={200: AssayElementSerializer})
    def get(self, request):
        assay = Assay.objects.first()
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
        assay = Assay.objects.first()
        error_message_list = []
        if assay:
            if all_list:
                assay.all = list(set(all_list))
            if disabled_list:
                assay.disabled = list(set(disabled_list))
            if hold_list:
                assay.hold = list(set(hold_list))
            for single_assay in assay.hold:
                if single_assay in assay.disabled:
                    error_message = "Assay {} is in both disabled and hold".format(single_assay)
                    error_message_list.append(error_message)
            combined_list = assay.hold + assay.disabled
            for single_assay in combined_list:
                if single_assay not in assay.all:
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
        created_jobs = []
        for request_id in request_ids:
            job = get_or_create_request_job(request_id)
            created_jobs.append(job)
        return Response({"details": "Import requests from LIMS jobs submitted %s" % str(request_ids)},
                        status=status.HTTP_201_CREATED)


class RequestIdLimsUpdateViewSet(GenericAPIView):
    serializer_class = RequestIdLimsPullSerializer

    logger = logging.getLogger(__name__)

    def post(self, request):
        request_ids = request.data['request_ids']
        for request_id in request_ids:
            logging.info("Submitting requestId %s to pipeline" % request_id)
            job = Job(run='beagle_etl.jobs.lims_etl_jobs.update_metadata', args={'request_id': request_id},
                      status=JobStatus.CREATED, max_retry=1, children=[],
                      callback='beagle_etl.jobs.lims_etl_jobs.request_callback',
                      callback_args={'request_id': request_id})

            job.save()
        return Response({"details": "Update requests from LIMS jobs submitted %s" % str(request_ids)},
                        status=status.HTTP_201_CREATED)
