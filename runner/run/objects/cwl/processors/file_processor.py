import os
from django.db import IntegrityError
from file_system.models import File, FileType, FileGroup, FileMetadata
from file_system.serializers import UpdateFileSerializer
from django.conf import settings
from runner.exceptions import FileHelperException, FileConflictException, FileUpdateException
from django.contrib.auth.models import User


class FileProcessor(object):

    @staticmethod
    def get_sample(file):
        return file.sample

    @staticmethod
    def get_file_id(uri):
        file_obj = FileProcessor.get_file_obj(uri)
        return str(file_obj.id)

    @staticmethod
    def get_file_path(uri):
        file_obj = FileProcessor.get_file_obj(uri)
        return file_obj.path

    @staticmethod
    def get_juno_uri_from_file(file):
        return 'juno://%s' % file.path

    @staticmethod
    def get_file_size(file):
        return file.size

    @staticmethod
    def get_file_checksum(file):
        return file.checksum

    @staticmethod
    def get_bid_from_file(file):
        return 'bid://%s' % str(file.id)

    @staticmethod
    def parse_path_from_uri(uri):
        if uri.startswith('bid://'):
            raise FileHelperException("Can't parse path from uri %s." % uri)
        elif uri.startswith('juno://'):
            return uri.replace('juno://', '')
        elif uri.startswith('file://'):
            return uri.replace('file://', '')
        else:
            raise FileHelperException("Unknown uri schema %s" % uri)

    @staticmethod
    def get_file_obj(uri):
        """
        :param uri:
        :return: File model. Throws UriParserException if File doesn't exist
        """
        if uri.startswith('bid://'):
            beagle_id = uri.replace('bid://', '')
            try:
                file_obj = File.objects.get(id=beagle_id)
            except File.DoesNotExist as e:
                raise FileHelperException("File with uri %s doesn't exist" % uri)
            return file_obj
        elif uri.startswith('juno://'):
            juno_path = uri.replace('juno://', '')
            file_obj = File.objects.filter(path=juno_path).first()
            if not file_obj:
                raise FileHelperException("File with uri %s doesn't exist" % uri)
            return file_obj
        elif uri.startswith('file://'):
            juno_path = uri.replace('file://', '')
            file_obj = File.objects.filter(path=juno_path).first()
            if not file_obj:
                raise FileHelperException("File with uri %s doesn't exist" % uri)
            return file_obj
        else:
            raise FileHelperException("Unknown uri schema %s" % uri)

    @staticmethod
    def create_file_obj(uri, size, checksum, group_id, metadata):
        file_path = FileProcessor.parse_path_from_uri(uri)
        basename = os.path.basename(file_path)
        file_type = FileProcessor.get_file_ext(basename)
        try:
            group_id_obj = FileGroup.objects.get(id=group_id)
        except FileGroup.DoesNotExist as e:
            raise FileHelperException('Invalid FileGroup id: %s' % group_id)
        file_object = File(path=file_path,
                           file_name=os.path.basename(file_path),
                           checksum=checksum,
                           file_type=file_type,
                           file_group=group_id_obj,
                           size=size)
        try:
            file_object.save()
        except IntegrityError as e:
            raise FileConflictException("File with path %s already exist" % file_path)
        file_metadata = FileMetadata(file=file_object, metadata=metadata)
        file_metadata.save()
        return file_object

    @staticmethod
    def get_file_ext(filename):
        """
        Return the proper FileType object based on extension
        :param filename:
        :return:
        """
        file_types = FileType.objects.all()
        for file_type in file_types:
            for ext in file_type.fileextension_set.all():
                if filename.endswith(ext.extension):
                    return file_type
        return FileType.objects.get(name='unknown')

    @staticmethod
    def update_file(file_object, path, metadata, user=None):
        data = {
            "path": path,
            "metadata": metadata,
        }
        try:
            user = User.objects.get(username=user)
            data['user'] = user.id
        except User.DoesNotExist:
            pass
        serializer = UpdateFileSerializer(file_object, data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            raise FileUpdateException(
                "Failed to update metadata for fastq files for %s : %s" % (path, serializer.errors))
