import logging
from .models import Job
from rest_framework import mixins
from rest_framework import status
from beagle.pagination import time_filter
from rest_framework.response import Response
from beagle_etl.jobs.lims_etl_jobs import TYPES
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import GenericViewSet
from beagle_etl.models import JobStatus, Job, Operator
from .serializers import JobSerializer, CreateJobSerializier, RequestIdLimsPullSerializer


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

    def list(self, request, *args, **kwargs):
        queryset = time_filter(Job, request.query_params)
        job_type = request.query_params.get('type')
        if job_type:
            if not TYPES.get(job_type):
                return Response({'details': 'Invalid job type: %s' % job_type}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(run=TYPES[job_type])
        sample_id = request.query_params.get('sample_id')
        if sample_id:
            queryset = queryset.filter(args__sample_id=sample_id)
        request_id = request.query_params.get('request_id')
        if request_id:
            queryset = queryset.filter(args__request_id=request_id)
        st = request.query_params.get('status')
        if st:
            queryset = queryset.filter(status=st)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)


class RequestIdLimsPullViewSet(GenericAPIView):
    serializer_class = RequestIdLimsPullSerializer

    logger = logging.getLogger(__name__)

    def post(self, request):
        request_ids = request.data['request_ids']
        for request_id in request_ids:
            logging.info("Submitting requestId %s to pipeline" % request_id)
            op = Operator.objects.first()
            if op.active:
                job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args={'request_id': request_id},
                          status=JobStatus.CREATED, max_retry=1, children=[],
                          callback='beagle_etl.jobs.lims_etl_jobs.request_callback',
                          callback_args={'request_id': request_id})
                job.save()
            else:
                job = Job(run='beagle_etl.jobs.lims_etl_jobs.fetch_samples', args={'request_id': request_id},
                          status=JobStatus.CREATED, max_retry=1, children=[])
                job.save()
        return Response({"details": "Import requests from lims jobs submitted %s"}, status=status.HTTP_201_CREATED)


