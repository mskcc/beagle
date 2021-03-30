from django.db.models import Q, Count
from file_system.models import FileMetadata, File
from file_system.exceptions import FileNotFoundException, InvalidQueryException

class FileRepository(object):

    @classmethod
    def all(cls):
        queryset = FileMetadata.objects.filter(latest=True).all()
        return queryset

    @classmethod
    def get(cls, id):
        try:
            return FileRepository.all().get(file_id=id)
        except FileMetadata.DoesNotExist:
            raise FileNotFoundException("File with id:%s does not exist" % str(id))

    @classmethod
    def delete(self, id):
        try:
            f = File.objects.get(id=id)
            f.delete()
        except File.DoesNotExist:
            raise FileNotFoundException("File with id:%s does not exist" % str(id))

    @classmethod
    def filter(cls, queryset=None, path=None, path_in=[], path_regex=None, file_type=None, file_type_in=[], file_name=None, file_name_in=[], file_name_regex=None, file_group=None, file_group_in=[], metadata={}, metadata_regex=[], q=None, values_metadata=None, values_metadata_list=[], filter_redact=False, exclude=[], order_by=None, distinct=None, metadata_distribution=None):
        if queryset == None:
            # If queryset not set, use all files
            queryset = FileRepository.all()
        if q:
            queryset = FileRepository.all()
            return queryset.filter(q)
        if (path and path_in) or (path and path_regex) or (path_in and path_regex):
            raise InvalidQueryException("Can't specify multiple path queries")
        if file_type and file_type_in:
            raise InvalidQueryException("Can't specify both file_type and file_type_in in the query")
        if file_group and file_group_in:
            raise InvalidQueryException("Can't specify both file_type and file_type_in in the query")
        if (file_name and file_name_in) or (file_name and file_name_regex) or (file_name_in and file_name_regex):
            raise InvalidQueryException("Can't specify multiple path queries")
        if metadata and metadata_regex:
            raise InvalidQueryException("Can't specify both metadata and metadata_regex in the query")
        if values_metadata and values_metadata_list:
            raise InvalidQueryException("Can't specify both values_metadata and values_metadata_list in the query")
        create_query_dict = {
            'file__path': path,
            'file__path__in': path_in,
            'file__path__regex': path_regex,
            'file__file_type__name': file_type,
            'file__file_type__name__in': file_type_in,
            'file__file_name': file_name,
            'file__file_name__in': file_name_in,
            'file__file_name__regex': file_name_regex,
            'file__file_group_id': file_group,
            'file__file_group_id__in': file_group_in
        }
        create_query_dict = {k: v for k, v in create_query_dict.items() if v}
        metadata_query_dict = dict()
        if metadata:
            for k, queries in metadata.items():
                if len(queries) > 1:
                    metadata_query_q = Q()
                    for single_query in queries:
                        single_query_dict = {'metadata__%s' % k: single_query}
                        metadata_query_q |= Q(**single_query_dict)
                    queryset = queryset.filter(metadata_query_q)
                else:
                    v = queries[0]
                    metadata_query_dict['metadata__%s' % k] = v
        elif metadata_regex:
            for single_regex_line in metadata_regex:
                regex_query_q = Q()
                for k,v in single_regex_line:
                    regex_query_dict = {'metadata__%s__regex' % k: v}
                    regex_query_q |= Q(**regex_query_dict)
                queryset = queryset.filter(regex_query_q)
        create_query_dict.update(metadata_query_dict)
        queryset = queryset.filter(
            Q(**create_query_dict) & Q(file__sample__redact=False)) if filter_redact else queryset.filter(
            **create_query_dict)
        if exclude:
            exc_dict = {}
            for single_exclude_field in exclude:
                exc_dict['metadata__%s__isnull' % single_exclude_field] = True
            queryset = queryset.exclude(**exc_dict)
        if distinct:
            distinct_query = 'metadata__%s' % distinct
            queryset = queryset.order_by(distinct_query).distinct(distinct_query)
        if order_by and not values_metadata_list:
            if distinct:
                metadata_ids = queryset.values_list('id', flat=True)
                queryset = FileRepository.all()
                queryset = queryset.filter(id__in=metadata_ids)
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by(order_by)
        if values_metadata:
            ret_str = 'metadata__%s' % values_metadata
            return queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
        if values_metadata_list:
            values_metadata_query_list = ['metadata__%s' % single_metadata for single_metadata in values_metadata_list]
            values_metadata_query_set = set(values_metadata_query_list)
            sorted_metadata_query_list = sorted(values_metadata_query_set)
            metadata_ids = queryset.values_list('id', flat=True)
            queryset = FileRepository.all()
            queryset = queryset.filter(id__in=metadata_ids)
            if order_by:
                queryset = queryset.order_by(order_by)
            return queryset.values_list(*sorted_metadata_query_list)
        if metadata_distribution:
            metadata_query = 'metadata__%s' % metadata_distribution
            metadata_ids = queryset.values_list('id',flat=True)
            queryset = FileRepository.all()
            queryset = queryset.filter(id__in=metadata_ids).values(metadata_query).annotate(Count(metadata_query))
        return queryset
