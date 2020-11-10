from file_system.models import Storage
from file_system.serializers import StorageSerializer, CreateStorageSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins


class StorageViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     GenericViewSet):
    queryset = Storage.objects.order_by('created_date').all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return StorageSerializer
        return CreateStorageSerializer
