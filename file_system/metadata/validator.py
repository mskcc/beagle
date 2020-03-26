from jsonschema import validate
from jsonschema.exceptions import ValidationError
from file_system.exceptions import MetadataValidationException


METADATA_SCHEMA = {
    "$id": "https://example.com/person.schema.json",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Metadata",
    "type": "object",
    # "required": ["requestId", "igoSampleId"],
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
            "type": ["null", "string"]
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
                "otherContactEmails": {
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
                        "type": ["null", "string"]
                    },
                    "barcodeIndex": {
                        "type": ["null", "string"]
                    },
                    "captureConcentrationNm": {
                        "type": ["null", "string"]
                    },
                    "captureInputNg": {
                        "type": ["null", "string"]
                    },
                    "captureName": {
                        "type": ["null", "string"]
                    },
                    "libaryIgoId": {
                        "type": ["null", "string"]
                    },
                    "libraryConcentrationNgul": {
                        "type": ["null", "number"]
                    },
                    "libraryVolume": {
                        "type": ["null", "integer"]
                    }
                }
            },
            "runs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "flowCellId": {
                            "type": ["null", "string"]
                        },
                        "flowCellLane": {
                            "type": ["null", "integer"]
                        },
                        "readLength": {
                            "type": ["null", "string"]
                        },
                        "runDate": {
                            "type": ["null", "string"]
                        },
                        "runId": {
                            "type": ["null", "string"]
                        },
                        "runMode": {
                            "type": ["null", "string"]
                        }
                    }
                }
            }
        },
        "oncoTreeCode": {
            "type": ["null", "string"]
        },
        "preservation": {
            "type": ["null", "string"]
        },
        "sampleOrigin": {
            "type": ["null", "string"]
        },
        "species": {
            "type": ["null", "string"]
        },
        "tissueLocation": {
            "type": ["null", "string"]
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
