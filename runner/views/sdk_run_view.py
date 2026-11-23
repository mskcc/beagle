from django.db.models import Prefetch
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from beagle.common import fix_query_list
from runner.models import Port, Run, RunStatus
from runner.serializers import SDKRunListSerializer, SDKRunSerializer


class SDKRunViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    """
    Runs with inputs and outputs resolved to file paths, for voyager-sdk operators.
    Listing requires at least one of run_ids, operator_run or job_groups.
    """

    serializer_class = SDKRunSerializer
    queryset = (
        Run.objects.select_related("app")
        .prefetch_related(Prefetch("port_set", queryset=Port.objects.order_by("name")), "samples")
        .order_by("created_date", "id")
    )

    @swagger_auto_schema(query_serializer=SDKRunListSerializer)
    def list(self, request, *args, **kwargs):
        query_params = fix_query_list(request.query_params, ["run_ids", "job_groups"])
        query = SDKRunListSerializer(data=query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)
        filters = query.validated_data
        if not (filters.get("run_ids") or filters.get("operator_run") or filters.get("job_groups")):
            return Response(
                {"detail": "Specify run_ids, operator_run or job_groups"}, status=status.HTTP_400_BAD_REQUEST
            )
        queryset = self.get_queryset()
        if filters.get("run_ids"):
            queryset = queryset.filter(id__in=filters["run_ids"])
        if filters.get("operator_run"):
            queryset = queryset.filter(operator_run_id=filters["operator_run"])
        if filters.get("job_groups"):
            queryset = queryset.filter(job_group__in=filters["job_groups"])
        if filters.get("status"):
            queryset = queryset.filter(status=RunStatus[filters["status"]].value)
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
