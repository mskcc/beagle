from django.conf import settings
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from beagle_etl.smile_message.objects.sample_object import SampleMetadata
from beagle_etl.exceptions import MissingDataException, ErrorInconsistentDataException


@dataclass
class RequestStatus:
    validationStatus: bool
    validationReport: str


@dataclass
class RequestMetadata:
    smileRequestId: str
    igoProjectId: str
    igoRequestId: str
    genePanel: str
    projectManagerName: str
    piEmail: str
    labHeadName: str
    labHeadEmail: str
    investigatorName: str
    investigatorEmail: str
    dataAnalystName: str
    dataAnalystEmail: str
    otherContactEmails: str
    dataAccessEmails: str
    qcAccessEmails: str
    strand: str
    libraryType: str
    isCmoRequest: bool
    bicAnalysis: bool
    status: RequestStatus
    requestJson: str
    samples: List['SampleMetadata'] = field(default_factory=list)
    igoDeliveryDate: Optional[str] = None
    ilabRequestId: Optional[str] = None
    pooledNormals: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestMetadata':
        """Deserialize from dictionary."""
        # Handle nested status
        status_data = data.get('status', {})
        status = RequestStatus(**status_data) if status_data else RequestStatus(False, "{}")

        # Handle nested samples
        samples_data = data.get('samples', [])
        samples = [SampleMetadata.from_dict(sample) for sample in samples_data]

        # Handle delivery date conversion
        delivery_date = None
        if data.get('igoDeliveryDate'):
            delivery_date = datetime.fromtimestamp(data["igoDeliveryDate"] / 1000).isoformat()

        return cls(
            smileRequestId=data.get('smileRequestId'), # required
            igoProjectId=data.get('igoProjectId'), # required
            igoRequestId=data.get('igoRequestId',), # required
            igoDeliveryDate=delivery_date,
            ilabRequestId=data.get('ilabRequestId'),
            genePanel=data.get('genePanel'), # required
            projectManagerName=data.get('projectManagerName', ''),
            piEmail=data.get('piEmail', ''),
            labHeadName=data.get('labHeadName', ''),
            labHeadEmail=data.get('labHeadEmail', ''),
            investigatorName=data.get('investigatorName', ''),
            investigatorEmail=data.get('investigatorEmail', ''),
            dataAnalystName=data.get('dataAnalystName', ''),
            dataAnalystEmail=data.get('dataAnalystEmail', ''),
            otherContactEmails=data.get('otherContactEmails', ''),
            dataAccessEmails=data.get('dataAccessEmails', ''),
            qcAccessEmails=data.get('qcAccessEmails', ''),
            strand=data.get('strand', 'null'),
            libraryType=data.get('libraryType'),
            isCmoRequest=data.get('isCmoRequest'), # required
            bicAnalysis=data.get('bicAnalysis'),
            status=status,
            requestJson=data.get('requestJson', ''),
            pooledNormals=data.get('pooledNormals', []),
            samples=samples
        )

    def __post_init__(self):
        """Validate request data after initialization."""
        self._validate_required_fields()
        self._validate_samples()
        self._validate_gene_panel_consistency()

    def to_dict(self, include_samples: bool = True) -> Dict[str, Any]:
        """
        Serialize RequestMetadata to dictionary with nested structure.

        Args:
            include_samples: If True, include all sample data. If False, only request-level metadata.

        Returns:
            Dictionary representation of the request
        """
        result = {
            'smileRequestId': self.smileRequestId,
            'igoProjectId': self.igoProjectId,
            'igoRequestId': self.igoRequestId,
            'igoDeliveryDate': self.igoDeliveryDate,
            'ilabRequestId': self.ilabRequestId,
            'genePanel': self.genePanel,
            'projectManagerName': self.projectManagerName,
            'piEmail': self.piEmail,
            'labHeadName': self.labHeadName,
            'labHeadEmail': self.labHeadEmail,
            'investigatorName': self.investigatorName,
            'investigatorEmail': self.investigatorEmail,
            'dataAnalystName': self.dataAnalystName,
            'dataAnalystEmail': self.dataAnalystEmail,
            'otherContactEmails': self.otherContactEmails,
            'dataAccessEmails': self.dataAccessEmails,
            'qcAccessEmails': self.qcAccessEmails,
            'strand': self.strand,
            'libraryType': self.libraryType,
            'isCmoRequest': self.isCmoRequest,
            'bicAnalysis': self.bicAnalysis,
            'pooledNormals': self.pooledNormals,
            'status': {
                'validationStatus': self.status.validationStatus,
                'validationReport': self.status.validationReport
            }
        }

        if include_samples:
            result['samples'] = [sample.to_dict() for sample in self.samples]

        return result

    def request_metadata(self) -> Dict[str, Any]:
        """
        Generate flattened request-level metadata for file creation.

        Returns:
            Dictionary with only request-level metadata fields
        """
        return {
            settings.REQUEST_ID_METADATA_KEY: self.igoRequestId,
            settings.PROJECT_ID_METADATA_KEY: self.igoProjectId,
            settings.RECIPE_METADATA_KEY: self.genePanel,
            'projectManagerName': self.projectManagerName,
            'piEmail': self.piEmail,
            settings.LAB_HEAD_NAME_METADATA_KEY: self.labHeadName,
            settings.LAB_HEAD_EMAIL_METADATA_KEY: self.labHeadEmail,
            settings.INVESTIGATOR_NAME_METADATA_KEY: self.investigatorName,
            settings.INVESTIGATOR_EMAIL_METADATA_KEY: self.investigatorEmail,
            'dataAnalystName': self.dataAnalystName,
            'dataAnalystEmail': self.dataAnalystEmail,
            'otherContactEmails': self.otherContactEmails,
            'dataAccessEmails': self.dataAccessEmails,
            'qcAccessEmails': self.qcAccessEmails,
        }

    def _validate_required_fields(self):
        """Validate that required request fields are not empty."""
        required_fields = {
            "smileRequestId": self.smileRequestId,
            "igoRequestId": self.igoRequestId,
            "igoProjectId": self.igoProjectId,
            "genePanel": self.genePanel,
        }

        for field_name, field_value in required_fields.items():
            if not field_value or field_value.strip() == '':
                raise MissingDataException(
                    f"Required field '{field_name}' is missing or empty for request"
                )

    def _validate_samples(self):
        """Validate that the request has samples."""
        if not self.samples:
            raise MissingDataException(
                f"Request {self.igoRequestId} has no samples"
            )

    def _validate_gene_panel_consistency(self):
        """Validate that all samples have the same gene panel as the request."""
        for sample in self.samples:
            if sample.genePanel != self.genePanel:
                raise ErrorInconsistentDataException(
                    f"Sample {sample.primaryId} has genePanel '{sample.genePanel}' "
                    f"which differs from request genePanel '{self.genePanel}'"
                )

    def validate_all_samples(self, redelivery: bool = False):
        """
        Validate all samples in the request with file system checks.

        Args:
            redelivery: If True, skip file conflict checks

        Raises:
            ErrorInconsistentDataException: If data is inconsistent
            MissingDataException: If required data is missing
            FailedToCopyFilePermissionDeniedException: If file permissions are bad
        """
        log = ""
        status = dict()
        for sample in self.samples:
            sample_log, sample_status = sample.validate_with_file_checks(redelivery=redelivery)
            log += sample_log
            status[sample_status.sample_id] = sample_status
        return log, status


