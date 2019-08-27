from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins, permissions
from file_system.models import FileType
from file_system.serializers import FileTypeSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated


class FileTypeView(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   GenericViewSet):
    queryset = FileType.objects.order_by('id').all()
    permission_classes = (IsAuthenticated,)
    serializer_class = FileTypeSerializer
    pagination_class = None
