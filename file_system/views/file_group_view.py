from file_system.models import FileGroup
from file_system.serializers import FileGroupSerializer, CreateFileGroupSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions
from rest_framework.permissions import IsAuthenticated


class FileGroupViewSet(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       GenericViewSet):
    queryset = FileGroup.objects.order_by('created_date').all()
    lookup_field = 'slug'
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return FileGroupSerializer
        return CreateFileGroupSerializer

