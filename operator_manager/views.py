from django.db import transaction
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from drf_yasg.utils import swagger_auto_schema
from operator_manager.models import Operator, OperatorStatus, OperatorVersion
from operator_manager.serializers import OperatorSerializer, OperatorQuerySerializer
from operator_manager.tasks import build_operator_image


class OperatorViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Operator.objects.select_related("notifier").order_by("id")
    serializer_class = OperatorSerializer
    filter_backends = ()

    def perform_create(self, serializer):
        operator = serializer.save()
        if operator.type == OperatorVersion.V2:
            self._schedule_build(operator)
        else:
            # Legacy operators live in the beagle codebase, there is no image to build
            operator.status = OperatorStatus.READY
            operator.save(update_fields=["status"])

    def perform_update(self, serializer):
        previous = (serializer.instance.github_url, serializer.instance.version, serializer.instance.type)
        operator = serializer.save()
        if operator.type == OperatorVersion.V2 and previous != (operator.github_url, operator.version, operator.type):
            operator.status = OperatorStatus.INSTALLING
            operator.save(update_fields=["status"])
            self._schedule_build(operator)

    @staticmethod
    def _schedule_build(operator):
        # Dispatch after commit so the worker is guaranteed to see the saved row
        transaction.on_commit(lambda: build_operator_image.delay(operator.id))

    @swagger_auto_schema(query_serializer=OperatorQuerySerializer)
    def list(self, request, *args, **kwargs):
        query = OperatorQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)
        params = query.validated_data
        queryset = self.get_queryset()
        if params.get("name"):
            queryset = queryset.filter(name=params["name"])
        if params.get("type"):
            queryset = queryset.filter(type=OperatorVersion[params["type"]].value)
        if params.get("status"):
            queryset = queryset.filter(status=OperatorStatus[params["status"]].value)
        if params.get("active") is not None:
            queryset = queryset.filter(active=params["active"])
        if params.get("trigger"):
            queryset = queryset.filter(trigger__contains=[params["trigger"]])
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)
