from rest_framework import mixins
from file_system.models import Sample
from file_system.serializers import SampleSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter


class SampleViewSet(mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    queryset = Sample.objects.order_by('-created_date').all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ('^sample_id',)

    def get_serializer_class(self):
        return SampleSerializer
