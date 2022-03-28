from rest_framework import mixins
from file_system.models import Patient
from file_system.serializers import PatientSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter


class PatientViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet
):
    queryset = Patient.objects.order_by("-created_date").all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ("^patient_id",)

    def get_serializer_class(self):
        return PatientSerializer
