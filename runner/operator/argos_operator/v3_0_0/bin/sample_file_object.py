import json

from .sample_metadata import SampleMetadata


class SampleFile:
    def __init__(self, path, metadata):
        self.path = path
        self.metadata = SampleMetadata(metadata)

    def __repr__(self):
        sample_metadata = self.metadata.get_metadata_argos_input()
        sample_metadata["path"] = self.path
        return json.dumps(sample_metadata, indent=2, sort_keys=True)
