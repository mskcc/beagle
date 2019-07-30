from file_system.models import File, FileMetadata
from file_system.serializers import FileSerializer, CreateFileSerializer
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, permissions
from django.db.models import Prefetch
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Max
from rest_framework.views import APIView
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework.settings import api_settings


class FileViewSet(APIView):
    serializer_class = FileSerializer
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get(self, request):
        """
        :return:
        """
        tags = request.query_params.get('tags', None)
        file_group = request.query_params.get('file_group', None)
        queryset = File.objects.order_by('created_date').prefetch_related(
            Prefetch('filemetadata_set',
                     queryset=FileMetadata.objects.select_related('file').order_by('-version'))).all()
        if tags:
            key, value = tags.split(':')
            filter_query = {'sample__metadata__' + key: value}
            queryset = File.objects.order_by('created_date').prefetch_related(
                Prefetch('filemetadata_set',
                         queryset=FileMetadata.objects.select_related('file').order_by('-version'))).filter(**filter_query).all()
        if file_group:
            queryset = queryset.filter(cohort__slug=file_group).all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        file = CreateFileSerializer(data=request.data)
        if file.is_valid():
            file.save()
            return Response(file.data, status=status.HTTP_201_CREATED)
        return Response(file.errors, status=status.HTTP_400_BAD_REQUEST)

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

