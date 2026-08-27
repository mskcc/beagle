from django.conf import settings
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from beagle_etl.models import ETLConfiguration, SMILEMessage, SmileMessageStatus
from beagle_etl.jobs.metadb_jobs import new_request
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    AssaySerializer,
    AssayElementSerializer,
    AssayUpdateSerializer,
    SMILEMessageSerializer,
    SMILEMessageListSerializer,
)


class ForceImportView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, _request, request_id):
        message = (
            SMILEMessage.objects.filter(request_id=request_id, topic=settings.METADB_NATS_NEW_REQUEST)
            .order_by("-created_date")
            .first()
        )
        if not message:
            return Response(
                {"detail": f"No new-request SMILEMessage found for request_id {request_id}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        new_request.delay(str(message.id), force_import=True)
        return Response(
            {"detail": f"Force import triggered for request {request_id} (message {message.id})."},
            status=status.HTTP_202_ACCEPTED,
        )


class SMILEMessageViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = SMILEMessage.objects.order_by("-created_date").all()
    serializer_class = SMILEMessageListSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(query_serializer=SMILEMessageListSerializer)
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = serializer.validated_data
        queryset = self.queryset
        if validated.get("request_id"):
            queryset = queryset.filter(request_id=validated["request_id"])
        if validated.get("topic"):
            queryset = queryset.filter(topic=validated["topic"])
        if validated.get("gene_panel"):
            queryset = queryset.filter(gene_panel=validated["gene_panel"])
        if validated.get("status"):
            queryset = queryset.filter(status=SmileMessageStatus[validated["status"]].value)
        page = self.paginate_queryset(queryset)
        serializer = SMILEMessageSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


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
        return Response({"errors": error_message_list}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AssayUpdateSerializer, responses={200: AssayElementSerializer})
    def post(self, request):
        request_data = dict(request.data)
        all_list = request_data.get("all")
        disabled_list = request_data.get("disabled")
        hold_list = request_data.get("hold")
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
                return Response({"errors": list(set(error_message_list))}, status=status.HTTP_400_BAD_REQUEST)
            assay.save()
            assay_response = AssaySerializer(assay)
            return Response(assay_response.data, status=status.HTTP_200_OK)
        error_message_list = ["Assay list is empty"]
        return Response({"errors": error_message_list}, status=status.HTTP_404_NOT_FOUND)
