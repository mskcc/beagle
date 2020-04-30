from file_system.models import FileMetadata
from file_system.exceptions import FileNotFoundException


class FileRepository(object):

    @classmethod
    def all(cls):
        metadata_ids = FileMetadata.objects.order_by('file', '-version').distinct('file_id').values_list('id',
                                                                                                         flat=True)
        queryset = FileMetadata.objects.filter(id__in=metadata_ids).all()
        return queryset

    @classmethod
    def get(cls, id):
        try:
            return FileRepository.all().get(file_id=id)
        except FileMetadata.DoesNotExist:
            raise FileNotFoundException("File with id:%s does not exist" % str(id))

    @classmethod
    def filter(cls, path=None, file_type=None, file_group=None, metadata={}):
        create_query_dict = {
            'file__path': path,
            'file__file_type': file_type,
            'file__file_group_id__in': file_group
        }
        create_query_dict = {k: v for k, v in create_query_dict.items() if v is not None}
        metadata_query_dict = dict()
        for k, v in metadata:
            metadata_query_dict['metadata_%s' % k] = v
        create_query_dict.update(metadata_query_dict)

        return FileRepository.all().filter(**create_query_dict)
