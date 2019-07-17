from file_system.models import FileMetadata
from file_system.serializers import Metadata, CreateMetadata
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions


class FileMetadataView(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     GenericViewSet):
    queryset = FileMetadata.objects.order_by('created_date').select_related('file').all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return Metadata
        return CreateMetadata
