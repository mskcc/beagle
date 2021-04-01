from rest_framework import mixins, status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response

from runner.models import OperatorRun, RunStatus
from runner.serializers import OperatorRunSerializer, OperatorRunListSerializer
from drf_yasg.utils import swagger_auto_schema

def query_from_dict(queryset, json_obj, query_filter):
    query = {query_filter % key: val for (key, val) in json_obj.items()}
    return queryset.filter(**query)

class OperatorRunViewSet(ReadOnlyModelViewSet):
    queryset = OperatorRun.objects.order_by("-created_date").distinct().all()
    serializer_class = OperatorRunListSerializer

    @swagger_auto_schema(query_serializer=OperatorRunListSerializer)
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        if serializer.is_valid():
            queryset = self.queryset
            if serializer.validated_data.get('status'):
                queryset = queryset.filter(status=RunStatus[serializer.validated_data.get('status')].value)
            if serializer.validated_data.get('app'):
                queryset = queryset.filter(operator__pipeline__id=serializer.validated_data.get('app'))
            if serializer.validated_data.get('app_name'):
                queryset = queryset.filter(operator__pipeline__name=serializer.validated_data.get('app_name'))
            if serializer.validated_data.get('app_version'):
                queryset = queryset.filter(operator__pipeline__version=serializer.validated_data.get('app_version'))
            if serializer.validated_data.get('tags'):
                queryset = query_from_dict(queryset, serializer.validated_data.get('tags'), "runs__tags__%s__contains")

            serializer = OperatorRunSerializer(self.paginate_queryset(queryset), many=True)
            return self.get_paginated_response(serializer.data)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
