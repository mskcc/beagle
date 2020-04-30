import uuid
from django.db.models import Prefetch
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from file_system.repository import FileRepository
from file_system.models import File, FileMetadata
from file_system.exceptions import FileNotFoundException
from file_system.serializers import CreateFileSerializer, UpdateFileSerializer, FileSerializer


class FileView(mixins.CreateModelMixin,
               mixins.DestroyModelMixin,
               mixins.RetrieveModelMixin,
               mixins.UpdateModelMixin,
               mixins.ListModelMixin,
               GenericViewSet):

    queryset = FileMetadata.objects.order_by('file', '-version').distinct('file')

    # File.objects.prefetch_related(
    #     Prefetch('filemetadata_set', queryset=FileMetadata.objects.raw('select md.* from file_system_filemetadata md inner join (select file_id, max(version) as maxversion FROM file_system_filemetadata group by file_id) groupedmd on md.file_id = groupedmd.file_id and md.version = groupedmd.maxversion;'))).first()

    permission_classes = (IsAuthenticated,)
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_serializer_class(self):
        return FileSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            f = FileRepository.get(kwargs['pk'])
        except FileNotFoundException as e:
            return Response({'details': str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = FileSerializer(f)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # queryset = File.objects.prefetch_related(
        #     Prefetch('filemetadata_set', queryset=
        #     FileMetadata.objects.select_related('file').order_by('-created_date'))).\
        #     order_by('file_name').all()
        metadata_ids = FileMetadata.objects.order_by('file', '-version').distinct('file_id').values_list('id',
                                                                                                         flat=True)
        file_groups = request.query_params.getlist('file_group')
        queryset = FileMetadata.objects.filter(id__in=metadata_ids)
        if file_groups:
            queryset = queryset.filter(file__file_group_id__in=file_groups)
        path = request.query_params.getlist('path')
        if path:
            queryset = queryset.filter(file__path__in=path)
        metadata = request.query_params.getlist('metadata')
        if metadata:
            filter_query = dict()
            for val in metadata:
                k, v = val.split(':')
                filter_query['metadata__%s' % k] = v
                queryset = queryset.filter(**filter_query)
        metadata_regex = request.query_params.getlist('metadata_regex')
        if metadata_regex:
            filter_query = dict()
            for val in metadata_regex:
                k, v = val.split(':')
                filter_query['metadata__%s__regex' % k] = v
                queryset = queryset.filter(**filter_query)
        filename = request.query_params.getlist('filename')
        if filename:
            queryset = queryset.filter(file__file_name__in=filename)
        filename_regex = request.query_params.get('filename_regex')
        if filename_regex:
            queryset = queryset.filter(file__file_name__regex=filename_regex)
        file_type = request.query_params.getlist('file_type')
        if file_type:
            queryset = queryset.filter(file__file_type__name__in=file_type)
        ret = request.query_params.get('return')
        if ret:
            ret_str = 'metadata__%s' % ret
            try:
                queryset = queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
            except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        page = self.paginate_queryset(queryset)
        if page is not None:
            if ret:
                return self.get_paginated_response(page)
            else:
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

