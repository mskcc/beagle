from file_system.models import File, Storage, FileGroup
from rest_framework import status
from rest_framework.response import Response
from file_system.serializers import FileSerializer, \
                                    CreateFileSerializer, \
                                    StorageSerializer, \
                                    CreateStorageSerializer, \
                                    FileGroupSerializer

from rest_framework import routers, serializers, viewsets
from rest_framework.decorators import api_view
# Create your views here.


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return FileSerializer
        return CreateFileSerializer


class StorageViewSet(viewsets.ModelViewSet):
    queryset = Storage.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return StorageSerializer
        return CreateStorageSerializer


@api_view(['GET', 'POST'])
def storage_view(request):
    if request.method == 'GET':
        storage = Storage.objects.all()
        serializer = StorageSerializer(storage, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = StorageSerializer(data=request.data)



