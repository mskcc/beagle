import os
from runner.models import Port
from file_system.models import File
from file_system.exceptions import FileNotFoundException
from file_system.repository.file_repository import FileRepository
from runner.serializers import PortSerializer, UpdatePortSerializer
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet


class PortViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = Port.objects.order_by('created_date').all()
    serializer_class = PortSerializer

    def update(self, request, *args, **kwargs):
        try:
            port = Port.objects.get(id=kwargs.get('pk'))
        except Port.DoesNotExist:
            return Response({'details': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
        value = request.data
        if isinstance(port.schema.get('type'), dict):
            if port.schema.get('type').get('type') == 'array':
                if port.schema.get('type').get('items') != 'File':
                    port.value = {"inputs": value.get('values')}
                else:
                    input_ids = []
                    files = []
                    for val in value.get('values'):
                        try:
                            file = FileRepository.get(id=val)
                        except FileNotFoundException:
                            return Response({'details': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
                        input_ids.append(val)
                        file_val = self._create_file(file, port.schema.get('secondaryFiles'))
                        files.append(file_val)
                    port.value = {
                        "refs": input_ids,
                        "inputs": files
                    }
        else:
            if port.schema.get('type') != 'File':
                port.value = {"inputs": value.get('values')}
            else:
                try:
                    file = FileRepository.get(pk=value.get('values')[0])
                except FileNotFoundException:
                    return Response({'details': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
                port.value = {"inputs": self._create_file(file, port.schema.get('secondaryFiles')), "refs": str(file.id)}
        port.save()
        response = PortSerializer(port)
        return Response(response.data, status=status.HTTP_200_OK)

    def _create_file(self, file_obj, secondary_files):
        cwl_file = {
            "class": "File",
            "path": file_obj.path,
            "location": file_obj.path,
            "basename": os.path.basename(file_obj.path),
            "size": file_obj.size
        }
        cwl_secondary_files = []
        for sf in secondary_files:
            sf_name = self._resolve_secondary_file(file_obj.path, sf)
            f = FileRepository.filter(path=sf_name).first()
            sf_file_obj = f.file
            cwl_secondary_file = self._create_file(sf_file_obj, [])
            cwl_secondary_files.append(cwl_secondary_file)
        cwl_file['secondaryFiles'] = cwl_secondary_files
        return cwl_file

    def _resolve_secondary_file(self, filename, suffix):
        while suffix.startswith('^'):
            suffix = suffix[1:]
            filename = os.path.splitext(filename)[0]
        return filename + suffix
