from django.conf import settings
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from file_system.models import Request
from file_system.serializers import RequestSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from beagle_etl.models import SMILEMessage
from beagle_etl.jobs.metadb_jobs import new_request


class RequestViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = Request.objects.order_by("-created_date").all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ("^request_id",)

    def get_serializer_class(self):
        return RequestSerializer


class ForceImportRequestView(APIView):
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
        new_request.apply_async(args=[str(message.id)], kwargs={"force": True}, queue=settings.BEAGLE_DEFAULT_QUEUE)
        return Response(
            {"detail": f"Force import triggered for request {request_id} (message {message.id})."},
            status=status.HTTP_202_ACCEPTED,
        )
