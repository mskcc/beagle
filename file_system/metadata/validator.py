from jsonschema import validate
from jsonschema.exceptions import ValidationError
from file_system.exceptions import MetadataValidationException


METADATA_SCHEMA = {
    "$id": "https://example.com/person.schema.json",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Metadata",
    "type": "object",
    "required": ["requestId", "igoSampleId"],
    "properties": {
        "igoSampleId": {
            "type": "string"
        },
        "requestId": {
            "type": "string"
        },
        "investigatorSampleId": {
            "type": "string"
        },
        "baitSet": {
            "type": "string"
        },
        "cmoPatientId": {
            "type": "string"
        },
        "collectionYear": {
            "type": "string"
        },
        "gender": {
            "type": "string"
        },
        "igoId": {
            "type": "string"
        },
        "requestMetadata": {
            "type": "object",
            "properties": {
                "dataAnalystEmail": {
                    "type": "string"
                },
                "dataAnalystName": {
                    "type": "string"
                },
                "investigatorEmail": {
                    "type": "string"
                },
                "investigatorName": {
                    "type": "string"
                },
                "labHeadEmail": {
                    "type": "string"
                },
                "labHeadName": {
                    "type": "string"
                },
                "projectManagerName": {
                    "type": "string"
                }
            }
        },
        "libraries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "barcodeId": {
                        "type": "string"
                    },
                    "barcodeIndex": {
                        "type": "string"
                    },
                    "captureConcentrationNm": {
                        "type": "string"
                    },
                    "captureInputNg": {
                        "type": "string"
                    },
                    "captureName": {
                        "type": "string"
                    },
                    "libaryIgoId": {
                        "type": "string"
                    },
                    "libraryConcentrationNgul": {
                        "type": "integer"
                    },
                    "libraryVolume": {
                        "type": "integer"
                    }
                }
            },
            "runs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "flowCellId": {
                            "type": "string"
                        },
                        "flowCellLane": {
                            "type": "integer"
                        },
                        "readLength": {
                            "type": "string"
                        },
                        "runDate": {
                            "type": "string"
                        },
                        "runId": {
                            "type": "string"
                        },
                        "runMode": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "oncoTreeCode": {
            "type": "string"
        },
        "preservation": {
            "type": "string"
        },
        "sampleOrigin": {
            "type": "string"
        },
        "species": {
            "type": "string"
        },
        "tissueLocation": {
            "type": "string"
        },
        "tumorOrNormal": {
            "type": "string"
        }
    }
}


class MetadataValidator(object):

    def __init__(self, schema=METADATA_SCHEMA):
        self.schema = schema

    def validate(self, data):
        try:
            validate(instance=data, schema=self.schema)
        except ValidationError as e:
            raise MetadataValidationException(e)


if __name__ == '__main__':
    validator = MetadataValidator(METADATA_SCHEMA)
    test = {
        "requestId": "REQUEST_ID",
        "igoSampleId": "SAMPLE"
    }
    try:
        validator.validate(test)
    except MetadataValidationException as e:
        print(e)
