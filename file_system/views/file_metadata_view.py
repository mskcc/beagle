from file_system.models import SampleMetadata
from file_system.serializers import Metadata, CreateMetadata
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions


class FileMetadataView(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = SampleMetadata.objects.order_by('created_date').select_related('sample').all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return Metadata
        return CreateMetadata
