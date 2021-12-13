from rest_framework import mixins
from drf_yasg.utils import swagger_auto_schema
from file_system.models import Sample
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.response import Response
from file_system.repository.file_repository import FileRepository
from file_system.serializers import SampleSerializer, FullSampleSerializer, SampleQuerySerializer


class SampleViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = Sample.objects.order_by("-created_date").all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ("^sample_id", "^sample_name", "^cmo_sample_name")

    def get_serializer_class(self):
        return SampleSerializer


class SampleFullViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Sample.objects.order_by("-created_date").all()
    permission_classes = (IsAuthenticated,)
    serializer_class = FullSampleSerializer

    @swagger_auto_schema(query_serializer=SampleQuerySerializer)
    def list(self, request, *args, **kwargs):
        request_id = request.query_params.get("project_id")
        if not request_id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        sample_ids = list(FileRepository.filter(metadata={"requestId": request_id}, values_metadata="sampleId").all())
        samples = Sample.objects.filter(sample_id__in=sample_ids)
        response = FullSampleSerializer(samples, many=True)
        return Response(response.data, status=status.HTTP_200_OK)
