from file_system.models import File, FileMetadata
from file_system.serializers import FileSerializer, CreateFileSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions
from django.db.models import Prefetch
from django.db.models import Max
from drf_multiple_model.views import ObjectMultipleModelAPIView


class FileViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  GenericViewSet):

    queryset = File.objects.order_by('created_date').prefetch_related(
        Prefetch('filemetadata_set', queryset=FileMetadata.objects.select_related('file').order_by('-version'))).all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return FileSerializer
        return CreateFileSerializer
