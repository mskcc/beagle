import json

from django.conf import settings

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_ID_METADATA_KEY,  # primaryId
    settings.PATIENT_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.CMO_SAMPLE_TAG_METADATA_KEY,  # ciTag
    settings.LIBRARY_ID_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
]


class SampleMetadata:
    def __init__(self, metadata):
        self.metadata = {k: metadata[k] for k in REQUIRED_KEYS if k in metadata}

    def get_metadata(self):
        return self.metadata

    def get_metadata_argos_input(self):
        d = dict()
        d["ID"] = self.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY]
        d["CN"] = self.metadata["sequencingCenter"]
        d["LB"] = self.metadata[settings.LIBRARY_ID_METADATA_KEY]
        d["PL"] = self.metadata["platform"]
        d["PU"] = self.metadata["barcodeIndex"]
        d["RG_ID"] = self.metadata["flowCellId"] + "_" + self.metadata["barcodeIndex"]
        d["request_id"] = self.metadata[settings.REQUEST_ID_METADATA_KEY]
        d["specimen_type"] = self.metadata[settings.SAMPLE_CLASS_METADATA_KEY]
        d["bwa_output"] = d["ID"] + ".bam"
        d["adapter"] = "AGATCGGAAGAGCACACGTCTGAACTCCAGTCACATGAGCATCTCGTATGCCGTCTTCTGCTTG"
        d["adapter2"] = "AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT"
        return d

    def __repr__(self):
        return json.dumps(self.metadata, indent=2, sort_keys=True)
