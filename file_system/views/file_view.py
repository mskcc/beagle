from django.db.models import Prefetch
from file_system.models import File, FileMetadata
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from file_system.serializers import FileSerializer, CreateFileSerializer, UpdateFileSerializer


class FileView(mixins.CreateModelMixin,
               mixins.DestroyModelMixin,
               mixins.RetrieveModelMixin,
               mixins.UpdateModelMixin,
               mixins.ListModelMixin,
               GenericViewSet):
    queryset = File.objects.prefetch_related(
            Prefetch('filemetadata_set', queryset=
            FileMetadata.objects.select_related('file').order_by('-created_date'))).\
            order_by('file_name').all()
    permission_classes = (IsAuthenticated,)
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return FileSerializer
        else:
            return CreateFileSerializer

    def list(self, request, *args, **kwargs):
        queryset = File.objects.prefetch_related(
            Prefetch('filemetadata_set', queryset=
            FileMetadata.objects.select_related('file').order_by('-created_date'))).\
            order_by('file_name').all()
        file_groups = request.query_params.getlist('file_group')
        if file_groups:
            queryset = queryset.filter(file_group_id__in=file_groups)
        metadata = request.query_params.getlist('metadata')
        if metadata:
            filter_query = dict()
            for val in metadata:
                k, v = val.split(':')
                filter_query['filemetadata__metadata__%s__regex' % k] = v
            queryset = queryset.filter(**filter_query)
        filename = request.query_params.getlist('filename')
        if filename:
            queryset = queryset.filter(file_name__in=filename)
        filename_regex = request.query_params.get('filename_regex')
        if filename_regex:
            queryset = queryset.filter(file_name__regex=filename_regex)
        file_type = request.query_params.getlist('file_type')
        if file_type:
            queryset = queryset.filter(file_type__ext__in=file_type)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FileSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CreateFileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            file = serializer.save()
            response = FileSerializer(file)
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            file = File.objects.get(id=kwargs.get('pk'))
        except File.DoesNotExist:
            return Response({'details': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateFileSerializer(file, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            file = File.objects.prefetch_related(
                Prefetch('filemetadata_set', queryset=
                FileMetadata.objects.select_related('file').order_by('-created_date'))).get(id=kwargs.get('pk'))
            response = FileSerializer(file)
            return Response(response.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

