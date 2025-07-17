from django.conf import settings

from .files_object import FilesObj
from .sample_metadata import SampleMetadata


class ArgosSample:
    def __init__(self, sample_name, file_list, file_type):
        self.sample_name = sample_name
        self.metadata = SampleMetadata(file_list, file_type)
        self.files_obj = FilesObj(file_list, file_type)
        self.file_type = self.files_obj.file_type
        self.sample_type = self.metadata.sample_type
        self.files = self.files_obj.get_files()
