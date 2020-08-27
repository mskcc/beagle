from file_system.models import FileMetadata, File
from file_system.exceptions import FileNotFoundException, InvalidQueryException


class FileRepository(object):

    @classmethod
    def all(cls, distinct=True):
        queryset = FileMetadata.objects.all()
        if distinct:
            queryset = FileRepository.distinct_files(queryset)
        return queryset

    @classmethod
    def distinct_files(cls, queryset):
        file_ids = queryset.values_list('file_id',flat=True)
        metadata_ids = FileMetadata.objects.filter(file_id__in=file_ids).order_by('file', '-version').distinct('file_id').values_list('id', flat=True)
        queryset = queryset.filter(id__in=metadata_ids).order_by('created_date').all()
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
    def filter(cls, queryset=None, path=None, path_in=[], path_regex=None, file_type=None, file_type_in=[], file_name=None, file_name_in=[], file_name_regex=None, file_group=None, file_group_in=[], metadata={}, metadata_regex={}, q=None, values_metadata=None, values_metadata_list=[], distinct=True):
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
            for k, v in metadata.items():
                metadata_query_dict['metadata__%s' % k] = v
        elif metadata_regex:
            for k, v in metadata.items():
                metadata_query_dict['metadata__%s__regex' % k] = v
        create_query_dict.update(metadata_query_dict)
        if queryset != None:
            queryset = queryset.filter(**create_query_dict)
        else:
            queryset = FileRepository.all().filter(**create_query_dict)
        if distinct:
            queryset = FileRepository.distinct_files(queryset)
        if values_metadata:
            ret_str = 'metadata__%s' % values_metadata
            return queryset.values_list(ret_str, flat=True).order_by(ret_str).distinct(ret_str)
        if values_metadata_list:
            values_metadata_query_list = ['metadata__%s' % single_metadata for single_metadata in values_metadata_list ]
            values_metadata_query_set = set(values_metadata_query_list)
            return queryset.values_list(*values_metadata_query_set).order_by(values_metadata_query_list[0]).distinct()

        return queryset
