import json

from django.conf import settings

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_ID_METADATA_KEY,
    settings.PATIENT_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,
    settings.CMO_SAMPLE_TAG_METADATA_KEY,
    "barcodeIndex",
    "flowCellId",
    "runMode",
]


class SampleMetadata:
    def __init__(self, metadata):
        self.metadata = {k: metadata[k] for k in REQUIRED_KEYS if k in metadata}

    def get_metadata(self):
        return self.metadata

    def get_metadata_argos_input(self):
        pass  # TODO - add json input format for this, as expected by ARGOS pipeline

    def __repr__(self):
        return json.dumps(self.metadata, indent=2, sort_keys=True)
