from file_system.models import FileMetadata
from file_system.serializers import Metadata, CreateMetadata
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins, permissions
from rest_framework.viewsets import GenericViewSet


class FileMetadataView(mixins.ListModelMixin,
                       mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       GenericViewSet):
    queryset = FileMetadata.objects.order_by('created_date').all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return Metadata
        return CreateMetadata

    def list(self, request, *args, **kwargs):
        file_id = request.query_params.get('file_id')
        if not file_id:
            return Response({'details': 'file_id needs to be specified'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = FileMetadata.objects.filter(file_id=file_id).order_by('created_date').all()
        page = self.paginate_queryset(queryset)
        if page:
            serializer = Metadata(page, many=True)
            return self.get_paginated_response(serializer.data)

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
