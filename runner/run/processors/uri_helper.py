from file_system.models import File, FileType
from runner.exceptions import UriParserException


class UriHelper(object):

    @staticmethod
    def get_file_id(uri):
        if uri.startswith('bid://'):
            beagle_id = uri.replace('bid://', '')
            try:
                file_obj = File.objects.get(id=beagle_id)
            except File.DoesNotExist as e:
                raise UriParserException("File with uri %s doesn't exist" % uri)
            return str(file_obj.id)
        elif uri.startswith('juno://'):
            juno_path = uri.replace('juno://', '')
            file_obj = File.objects.filter(path=juno_path).first()
            if not file_obj:
                raise UriParserException("File with uri %s doesn't exist" % uri)
            return str(file_obj.id)
        else:
            raise UriParserException("Unknown uri schema %s" % uri)
