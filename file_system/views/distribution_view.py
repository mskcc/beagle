from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from beagle.common import fix_query_list
from beagle.pagination import time_filter
from file_system.models import FileMetadata
from file_system.repository import FileRepository
from file_system.serializers import DistributionQuerySerializer


class DistributionView(mixins.ListModelMixin,
                       GenericViewSet):
    queryset = FileMetadata.objects.order_by('file', '-version').distinct('file')
    permission_classes = (IsAuthenticated,)
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    @swagger_auto_schema(query_serializer=DistributionQuerySerializer)
    def list(self, request, *args, **kwargs):
        query_list_types = ['file_group', 'path', 'metadata', 'metadata_regex', 'filename', 'file_type',
                            'values_metadata', 'exclude_null_metadata']
        fixed_query_params = fix_query_list(request.query_params, query_list_types)
        serializer = DistributionQuerySerializer(data=fixed_query_params)
        if serializer.is_valid():
            queryset = FileRepository.all()
            queryset = time_filter(FileMetadata, request.query_params,
                                   time_modal='modified_date',
                                   previous_queryset=queryset)
            file_group = fixed_query_params.get('file_group')
            path = fixed_query_params.get('path')
            metadata = fixed_query_params.get('metadata')
            metadata_regex = fixed_query_params.get('metadata_regex')
            path_regex = fixed_query_params.get('path_regex')
            filename = fixed_query_params.get('filename')
            filename_regex = fixed_query_params.get('filename_regex')
            file_type = fixed_query_params.get('file_type')
            values_metadata = fixed_query_params.get('values_metadata')
            metadata_distribution = fixed_query_params.get('metadata_distribution')
            exclude_null_metadata = fixed_query_params.get('exclude_null_metadata')
            order_by = fixed_query_params.get('order_by')
            distinct_metadata = fixed_query_params.get('distinct_metadata')
            kwargs = {'queryset':queryset}
            if file_group:
                if len(file_group) == 1:
                    kwargs['file_group'] = file_group[0]
                else:
                    kwargs['file_group_in'] = file_group
            if path:
                if len(path) == 1:
                    kwargs['path'] = path[0]
                else:
                    kwargs['path_in'] = path
            if metadata:
                filter_query = dict()
                for val in metadata:
                    k, v = val.split(':')
                    metadata_field = k.strip()
                    if metadata_field not in filter_query:
                        filter_query[metadata_field] = [v.strip()]
                    else:
                        filter_query[metadata_field].append(v.strip())
                if filter_query:
                    kwargs['metadata'] = filter_query
            if metadata_regex:
                filter_query = []
                for single_reqex_query in metadata_regex:
                    single_value = single_reqex_query.split('|')
                    single_reqex_filters = []
                    for val in single_value:
                        k, v = val.split(':')
                        single_reqex_filters.append((k.strip(), v.strip()))
                    filter_query.append(single_reqex_filters)
                if filter_query:
                    kwargs['metadata_regex'] = filter_query
            if path_regex:
                kwargs['path_regex'] = path_regex
            if filename:
                if len(filename) == 1:
                    kwargs['file_name'] = filename[0]
                else:
                    kwargs['file_name_in'] = filename
            if filename_regex:
                kwargs['file_name_regex'] = filename_regex
            if file_type:
                if len(file_type) == 1:
                    kwargs['file_type'] = file_type[0]
                else:
                    kwargs['file_type_in'] = file_type
            kwargs['metadata_distribution'] = metadata_distribution
            if exclude_null_metadata:
                kwargs['exclude'] = exclude_null_metadata
            if order_by:
                kwargs['order_by'] = order_by
            if distinct_metadata:
                kwargs['distinct'] = distinct_metadata
            if values_metadata:
                if len(values_metadata) == 1:
                    kwargs['values_metadata'] = values_metadata[0]
                else:
                    kwargs['values_metadata_list'] = values_metadata
            try:
                queryset = FileRepository.filter(**kwargs)
            except Exception as e:
                return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            distribution_dict = {}
            for single_metadata in queryset:
                single_metadata_name = None
                single_metadata_count = 0
                for single_key, single_value in single_metadata.items():
                    if 'count' in single_key:
                        single_metadata_count = single_value
                    else:
                        single_metadata_name = single_value
                if single_metadata_name is not None:
                    distribution_dict[single_metadata_name] = single_metadata_count
            return Response(distribution_dict, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
