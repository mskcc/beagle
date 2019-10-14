from beagle_etl.jobs.lims_etl_jobs import TYPES
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .models import Job
from .serializers import JobSerializer, CreateJobSerialzier


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
            return CreateJobSerialzier

    def create(self, request, *args, **kwargs):
        pass

    def list(self, request, *args, **kwargs):
        queryset = Job.objects.order_by('created_date').all()
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
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = JobSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

