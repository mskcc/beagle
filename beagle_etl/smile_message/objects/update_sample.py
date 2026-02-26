from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from beagle_etl.smile_message.objects.sample_object import SampleMetadata, SampleAlias, PatientAlias


@dataclass
class PatientAliasValue:
    """Patient alias with value and namespace."""

    value: str
    namespace: str


@dataclass
class PatientInfo:
    """Patient information in update sample message."""

    smilePatientId: str
    patientAliases: List[PatientAlias]
    cmoPatientId: PatientAliasValue

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatientInfo":
        """Deserialize PatientInfo from dictionary."""
        patient_aliases_data = data.get("patientAliases", [])
        patient_aliases = [PatientAlias(**alias) for alias in patient_aliases_data]

        cmo_patient_id_data = data.get("cmoPatientId", {})
        cmo_patient_id = PatientAliasValue(**cmo_patient_id_data)

        return cls(
            smilePatientId=data.get("smilePatientId"), patientAliases=patient_aliases, cmoPatientId=cmo_patient_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert PatientInfo to dictionary."""
        return {
            "smilePatientId": self.smilePatientId,
            "patientAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.patientAliases],
            "cmoPatientId": {"value": self.cmoPatientId.value, "namespace": self.cmoPatientId.namespace},
        }


@dataclass
class UpdateSample:
    """Update sample message containing patient and sample metadata list."""

    smileSampleId: str
    sampleAliases: List[SampleAlias]
    patient: PatientInfo
    sampleMetadataList: List[SampleMetadata]
    sampleClass: str
    sampleCategory: str
    datasource: str
    revisable: bool
    primarySampleAlias: str
    latestSampleMetadata: SampleMetadata
    tempo: Optional[Any] = None
    dbGap: Optional[Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UpdateSample":
        """Deserialize UpdateSample from dictionary."""
        # Handle sample aliases
        sample_aliases_data = data.get("sampleAliases", [])
        sample_aliases = [SampleAlias(**alias) for alias in sample_aliases_data]

        # Handle patient info
        patient_data = data.get("patient", {})
        patient = PatientInfo.from_dict(patient_data)

        # Get IDs from root level to inject into metadata
        smile_sample_id = data.get("smileSampleId")
        smile_patient_id = patient_data.get("smilePatientId")

        # Handle sample metadata list - inject IDs if missing
        sample_metadata_list_data = data.get("sampleMetadataList", [])
        sample_metadata_list = []
        for sample_data in sample_metadata_list_data:
            # Inject smileSampleId and smilePatientId if not present
            if "smileSampleId" not in sample_data and smile_sample_id:
                sample_data["smileSampleId"] = smile_sample_id
            if "smilePatientId" not in sample_data and smile_patient_id:
                sample_data["smilePatientId"] = smile_patient_id
            sample_metadata_list.append(SampleMetadata.from_dict(sample_data))

        # Handle latest sample metadata - inject IDs if missing
        latest_sample_metadata_data = data.get("latestSampleMetadata", {})
        if "smileSampleId" not in latest_sample_metadata_data and smile_sample_id:
            latest_sample_metadata_data["smileSampleId"] = smile_sample_id
        if "smilePatientId" not in latest_sample_metadata_data and smile_patient_id:
            latest_sample_metadata_data["smilePatientId"] = smile_patient_id
        latest_sample_metadata = SampleMetadata.from_dict(latest_sample_metadata_data)

        return cls(
            smileSampleId=smile_sample_id,
            sampleAliases=sample_aliases,
            patient=patient,
            sampleMetadataList=sample_metadata_list,
            tempo=data.get("tempo"),
            dbGap=data.get("dbGap"),
            sampleClass=data.get("sampleClass"),
            sampleCategory=data.get("sampleCategory"),
            datasource=data.get("datasource"),
            revisable=data.get("revisable"),
            primarySampleAlias=data.get("primarySampleAlias"),
            latestSampleMetadata=latest_sample_metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert UpdateSample to dictionary."""
        return {
            "smileSampleId": self.smileSampleId,
            "sampleAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.sampleAliases],
            "patient": self.patient.to_dict(),
            "sampleMetadataList": [sample.to_dict() for sample in self.sampleMetadataList],
            "tempo": self.tempo,
            "dbGap": self.dbGap,
            "sampleClass": self.sampleClass,
            "sampleCategory": self.sampleCategory,
            "datasource": self.datasource,
            "revisable": self.revisable,
            "primarySampleAlias": self.primarySampleAlias,
            "latestSampleMetadata": self.latestSampleMetadata.to_dict(),
        }
