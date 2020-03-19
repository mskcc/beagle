import json
from notifier.event_handler.event import Event


class ETLImportEvent(Event):

    def __init__(self, request_id, imported_files, pooled_normals):
        self.request_id = request_id
        self.imported_files = imported_files
        self.pooled_normals = pooled_normals

    @classmethod
    def get_type(cls):
        return "ETLImportEvent"

    @classmethod
    def get_method(cls):
        return "process_import_event"

    def __str__(self):
        description = "Request imported: %s\n" % self.request_id
        file_list = "List of fastqs:\n"
        for f in self.imported_files:
            file_list += "%s: %s\n" % (f[0], f[1])
        description += file_list
        pooled_normals_list = "List of pooled normals:\n"
        for f in self.pooled_normals:
            pooled_normals_list += "%s\n" % f.path
        description += pooled_normals_list
        return description
