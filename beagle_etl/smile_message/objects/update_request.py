from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json
from beagle_etl.smile_message.objects.request_object import RequestMetadata


@dataclass
class RequestStatus:
    """Request validation status."""

    validationStatus: bool
    validationReport: str


@dataclass
class UpdateRequestMetadata:
    """
    Update request metadata item.

    Contains request metadata updates with a deserialized RequestMetadata object.
    """

    igoRequestId: str
    requestMetadataJson: RequestMetadata
    importDate: str
    status: RequestStatus

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UpdateRequestMetadata":
        """Deserialize UpdateRequestMetadata from dictionary."""
        # Handle nested status
        status_data = data.get("status", {})
        status = RequestStatus(**status_data) if status_data else RequestStatus(False, "{}")

        # Get igoRequestId from parent level
        igo_request_id = data.get("igoRequestId")

        # Deserialize requestMetadataJson into RequestMetadata object
        request_metadata_raw = data.get("requestMetadataJson")
        if isinstance(request_metadata_raw, str):
            request_metadata_dict = json.loads(request_metadata_raw)
        else:
            request_metadata_dict = request_metadata_raw

        # Rename fields to match RequestMetadata expected names
        if "requestId" in request_metadata_dict:
            request_metadata_dict["igoRequestId"] = request_metadata_dict.pop("requestId")
        if "projectId" in request_metadata_dict:
            request_metadata_dict["igoProjectId"] = request_metadata_dict.pop("projectId")
        if "recipe" in request_metadata_dict:
            request_metadata_dict["genePanel"] = request_metadata_dict.pop("recipe")
        if "deliveryDate" in request_metadata_dict:
            request_metadata_dict["igoDeliveryDate"] = request_metadata_dict.pop("deliveryDate")

        # Remove fields that RequestMetadata doesn't use
        fields_to_remove = ["requestName", "neoAg", "deliveryPath"]
        for field in fields_to_remove:
            request_metadata_dict.pop(field, None)

        request_metadata = RequestMetadata.from_dict(request_metadata_dict)

        return cls(
            igoRequestId=igo_request_id,
            requestMetadataJson=request_metadata,
            importDate=data.get("importDate"),
            status=status,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert UpdateRequestMetadata to dictionary."""
        return {
            "igoRequestId": self.igoRequestId,
            "requestMetadataJson": json.dumps(self.requestMetadataJson.to_dict()),
            "importDate": self.importDate,
            "status": {
                "validationStatus": self.status.validationStatus,
                "validationReport": self.status.validationReport,
            },
        }


@dataclass
class UpdateRequest:
    """
    Update request message containing a list of request metadata updates.

    Represents updates to a request over time, with multiple versions of metadata.
    """

    updates: List[UpdateRequestMetadata]

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "UpdateRequest":
        """
        Deserialize UpdateRequest from a list of dictionaries.

        Args:
            data: List of request metadata update dictionaries

        Returns:
            UpdateRequest object
        """
        updates = [UpdateRequestMetadata.from_dict(item) for item in data]
        return cls(updates=updates)

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Convert UpdateRequest to a list of dictionaries.

        Returns:
            List of request metadata update dictionaries
        """
        return [update.to_dict() for update in self.updates]

    def get_latest_update(self) -> Optional[UpdateRequestMetadata]:
        """
        Get the most recent update (last item in the list).

        Returns:
            The latest UpdateRequestMetadata or None if list is empty
        """
        return self.updates[-1] if self.updates else None

    def get_updates_by_request_id(self, igo_request_id: str) -> List[UpdateRequestMetadata]:
        """
        Filter updates by igoRequestId.

        Args:
            igo_request_id: The request ID to filter by

        Returns:
            List of updates matching the request ID
        """
        return [update for update in self.updates if update.igoRequestId == igo_request_id]
