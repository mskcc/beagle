from rest_framework import mixins
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response

from runner.models import OperatorRun
from runner.serializers import OperatorRunSerializer


class OperatorRunViews(mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):

    queryset = OperatorRun.objects.order_by('-created_date').all()
    serializer_class = OperatorRunSerializer

    def list(self, request, *args, **kwargs):
        queryset = OperatorRun.objects.order_by('-created_date').all()
        job_group = request.query_params.getlist('job_group')
        if job_group:
            queryset = queryset.filter(job_group__in=job_group).all()
        page = self.paginate_queryset(queryset)
        if page:
            response = OperatorRunSerializer(page, many=True)
            return self.get_paginated_response(response.data)
        return Response([], status=status.HTTP_200_OK)
