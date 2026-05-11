import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from django.conf import settings
from beagle_etl.exceptions import (
    ErrorInconsistentDataException,
    MissingDataException,
    IncorrectlyFormattedPrimaryId,
    FailedToCopyFilePermissionDeniedException,
    FailedToFetchSampleException,
    ETLExceptions,
)
from runner.operator.helper import format_sample_name
from beagle_etl.smile_message.objects.validation import SampleStatus
from file_system.models import File
from beagle_etl.jobs.helper_jobs import check_file_permissions, fix_path_iris

logger = logging.getLogger(__name__)


@dataclass
class SampleStatusObj:
    validationStatus: bool
    validationReport: str


@dataclass
class CmoSampleIdFields:
    naToExtract: str
    normalizedPatientId: str
    sampleType: str
    recipe: str


@dataclass
class SampleAlias:
    value: str
    namespace: str


@dataclass
class PatientAlias:
    value: str
    namespace: str


@dataclass
class Run:
    runMode: str
    runId: str
    flowCellId: str
    readLength: str
    runDate: str
    flowCellLanes: List[int]
    fastqs: List[str]

    def __post_init__(self):
        """Validate run data after initialization."""
        if not self.fastqs:
            raise MissingDataException(f"Run {self.runId} has no fastq files")
        if not self.runId:
            raise MissingDataException("Run must have a runId")

    def to_dict(self) -> Dict[str, Any]:
        """Convert Run object to dictionary."""
        return {
            "runMode": self.runMode,
            "runId": self.runId,
            "flowCellId": self.flowCellId,
            "readLength": self.readLength,
            "runDate": self.runDate,
            "flowCellLanes": self.flowCellLanes,
            "fastqs": self.fastqs,
        }


@dataclass
class Library:
    libraryIgoId: str
    libraryVolume: float
    libraryConcentrationNgul: float
    captureConcentrationNm: str
    captureInputNg: str
    captureName: str
    runs: List[Run]
    barcodeId: Optional[str] = None
    barcodeIndex: Optional[str] = None
    dnaInputNg: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Library":
        """Deserialize Library from dictionary."""
        runs_data = data.get("runs", [])
        runs = [Run(**run) for run in runs_data]

        return cls(
            barcodeId=data.get("barcodeId"),
            barcodeIndex=data.get("barcodeIndex"),
            libraryIgoId=data.get("libraryIgoId", ""),
            libraryVolume=data.get("libraryVolume"),
            libraryConcentrationNgul=data.get("libraryConcentrationNgul"),
            dnaInputNg=data.get("dnaInputNg"),
            captureConcentrationNm=data.get("captureConcentrationNm", ""),
            captureInputNg=data.get("captureInputNg", ""),
            captureName=data.get("captureName", ""),
            runs=runs,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Library object to dictionary."""
        return {
            "barcodeId": self.barcodeId,
            "barcodeIndex": self.barcodeIndex,
            "libraryIgoId": self.libraryIgoId,
            "libraryVolume": self.libraryVolume,
            "libraryConcentrationNgul": self.libraryConcentrationNgul,
            "dnaInputNg": self.dnaInputNg,
            "captureConcentrationNm": self.captureConcentrationNm,
            "captureInputNg": self.captureInputNg,
            "captureName": self.captureName,
            "runs": [run.to_dict() for run in self.runs],
        }


@dataclass
class SampleMetadata:
    smileSampleId: str
    smilePatientId: str
    primaryId: str
    cmoPatientId: str
    cmoSampleName: str
    sampleName: str
    investigatorSampleId: str
    importDate: str
    sampleType: str
    species: str
    sex: str
    tumorOrNormal: str
    sampleClass: str
    tissueLocation: str
    genePanel: str
    baitSet: str
    datasource: str
    igoComplete: bool
    status: SampleStatusObj
    cmoSampleIdFields: CmoSampleIdFields
    qcReports: List[Any]
    libraries: List[Library]
    sampleAliases: List[SampleAlias]
    patientAliases: List[PatientAlias]
    additionalProperties: Dict[str, str]
    preservation: Optional[str] = None
    sampleOrigin: Optional[str] = None
    igoRequestId: Optional[str] = None
    oncotreeCode: Optional[str] = None
    collectionYear: Optional[str] = None
    tubeId: Optional[str] = None
    cfDNA2dBarcode: Optional[str] = None
    cmoInfoIgoId: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SampleMetadata":
        """Deserialize SampleMetadata from dictionary."""
        # Handle nested status
        status_data = data.get("status", {})
        status = SampleStatusObj(**status_data) if status_data else SampleStatusObj(False, "{}")

        # Handle nested cmoSampleIdFields
        cmo_fields_data = data.get("cmoSampleIdFields", {})
        cmo_fields = CmoSampleIdFields(**cmo_fields_data) if cmo_fields_data else CmoSampleIdFields("", "", "", "")

        # Handle libraries
        libraries_data = data.get("libraries", [])
        libraries = [Library.from_dict(lib) for lib in libraries_data]

        # Handle sample aliases
        sample_aliases_data = data.get("sampleAliases", [])
        sample_aliases = [SampleAlias(**alias) for alias in sample_aliases_data]

        # Handle patient aliases
        patient_aliases_data = data.get("patientAliases", [])
        patient_aliases = [PatientAlias(**alias) for alias in patient_aliases_data]

        return cls(
            smileSampleId=data.get("smileSampleId"),  # required
            smilePatientId=data.get("smilePatientId"),  # required
            primaryId=data.get("primaryId"),  # required
            cmoPatientId=data.get("cmoPatientId"),  # required
            cmoSampleName=data.get("cmoSampleName"),  # required
            sampleName=data.get("sampleName"),  # required
            cmoInfoIgoId=data.get("cmoInfoIgoId"),
            investigatorSampleId=data.get("investigatorSampleId"),
            igoRequestId=data.get("igoRequestId"),
            importDate=data.get("importDate"),
            sampleType=data.get("sampleType"),  # required
            oncotreeCode=data.get("oncotreeCode"),
            collectionYear=data.get("collectionYear"),
            tubeId=data.get("tubeId"),
            cfDNA2dBarcode=data.get("cfDNA2dBarcode"),
            species=data.get("species"),
            sex=data.get("sex"),
            tumorOrNormal=data.get("tumorOrNormal"),  # required
            preservation=data.get("preservation"),  # required
            sampleClass=data.get("sampleClass"),  # required
            sampleOrigin=data.get("sampleOrigin"),
            tissueLocation=data.get("tissueLocation"),
            genePanel=data.get("genePanel"),  # required
            baitSet=data.get("baitSet"),  # required
            datasource=data.get("datasource") or "igo",
            igoComplete=data.get("igoComplete"),
            status=status,
            cmoSampleIdFields=cmo_fields,
            qcReports=data.get("qcReports", []),
            libraries=libraries,
            sampleAliases=sample_aliases,
            patientAliases=patient_aliases,
            additionalProperties=data.get("additionalProperties", {}),
        )

    def __post_init__(self):
        """Validate sample data after initialization."""
        self._validate_primary_id()
        self._validate_required_fields()

    def to_dict(self) -> Dict[str, Any]:
        """Convert SampleMetadata object to dictionary with nested structure."""
        return {
            "smileSampleId": self.smileSampleId,
            "smilePatientId": self.smilePatientId,
            "primaryId": self.primaryId,
            "cmoPatientId": self.cmoPatientId,
            "cmoSampleName": self.cmoSampleName,
            "sampleName": self.sampleName,
            "investigatorSampleId": self.investigatorSampleId,
            "igoRequestId": self.igoRequestId,
            "cmoInfoIgoId": self.cmoInfoIgoId,
            "importDate": self.importDate,
            "sampleType": self.sampleType,
            "oncotreeCode": self.oncotreeCode,
            "collectionYear": self.collectionYear,
            "tubeId": self.tubeId,
            "cfDNA2dBarcode": self.cfDNA2dBarcode,
            "species": self.species,
            "sex": self.sex,
            "tumorOrNormal": self.tumorOrNormal,
            "preservation": self.preservation,
            "sampleClass": self.sampleClass,
            "sampleOrigin": self.sampleOrigin,
            "tissueLocation": self.tissueLocation,
            "genePanel": self.genePanel,
            "baitSet": self.baitSet,
            "datasource": self.datasource,
            "igoComplete": self.igoComplete,
            "status": {
                "validationStatus": self.status.validationStatus,
                "validationReport": self.status.validationReport,
            },
            "cmoSampleIdFields": {
                "naToExtract": self.cmoSampleIdFields.naToExtract,
                "normalizedPatientId": self.cmoSampleIdFields.normalizedPatientId,
                "sampleType": self.cmoSampleIdFields.sampleType,
                "recipe": self.cmoSampleIdFields.recipe,
            },
            "qcReports": self.qcReports,
            "libraries": [lib.to_dict() for lib in self.libraries],
            "sampleAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.sampleAliases],
            "patientAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.patientAliases],
            "additionalProperties": self.additionalProperties,
        }

    def sample_metadata(self, library: "Library", run: "Run", fastq: str) -> Dict[str, Any]:
        """
        Generate flattened sample metadata with library and run data for file creation.

        Args:
            library: Library object to flatten
            run: Run object to flatten
            fastq: Fastq filename for determining R1/R2

        Returns:
            Flattened dictionary with sample, library, and run metadata at top level
        """
        from beagle_etl.jobs.helper_jobs import R1_or_R2

        result = {
            "smileSampleId": self.smileSampleId,
            "smilePatientId": self.smilePatientId,
            "primaryId": self.primaryId,
            "cmoPatientId": self.cmoPatientId,
            "cmoSampleName": self.cmoSampleName,
            "sampleName": self.sampleName,
            "investigatorSampleId": self.investigatorSampleId,
            "cmoInfoIgoId": self.cmoInfoIgoId,
            "importDate": self.importDate,
            "sampleType": self.sampleType,
            "oncotreeCode": self.oncotreeCode,
            "collectionYear": self.collectionYear,
            "tubeId": self.tubeId,
            "cfDNA2dBarcode": self.cfDNA2dBarcode,
            "species": self.species,
            "sex": self.sex,
            "tumorOrNormal": self.tumorOrNormal,
            "preservation": self.preservation,
            "sampleClass": self.sampleClass,
            "sampleOrigin": self.sampleOrigin,
            "tissueLocation": self.tissueLocation,
            "genePanel": self.genePanel,
            "baitSet": self.baitSet,
            "datasource": self.datasource,
            "igoComplete": self.igoComplete,
            "status": {
                "validationStatus": self.status.validationStatus,
                "validationReport": self.status.validationReport,
            },
            "cmoSampleIdFields": {
                "naToExtract": self.cmoSampleIdFields.naToExtract,
                "normalizedPatientId": self.cmoSampleIdFields.normalizedPatientId,
                "sampleType": self.cmoSampleIdFields.sampleType,
                "recipe": self.cmoSampleIdFields.recipe,
            },
            "qcReports": self.qcReports,
            "sampleAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.sampleAliases],
            "patientAliases": [{"value": alias.value, "namespace": alias.namespace} for alias in self.patientAliases],
            "additionalProperties": self.additionalProperties,
            # Flattened library metadata
            "barcodeId": library.barcodeId,
            "barcodeIndex": library.barcodeIndex,
            "libraryIgoId": library.libraryIgoId,
            "libraryVolume": library.libraryVolume,
            "libraryConcentrationNgul": library.libraryConcentrationNgul,
            "dnaInputNg": library.dnaInputNg,
            "captureConcentrationNm": library.captureConcentrationNm,
            "captureInputNg": library.captureInputNg,
            "captureName": library.captureName,
            # Flattened run metadata
            "runMode": run.runMode,
            "runId": run.runId,
            "flowCellId": run.flowCellId,
            "readLength": run.readLength,
            "runDate": run.runDate,
            "flowCellLanes": run.flowCellLanes,
            # R1/R2 based on fastq filename
            "R": R1_or_R2(fastq),
            "ciTag": format_sample_name(self.cmoSampleName, self.sampleClass),
            "sequencingCenter": "MSKCC",
            "platform": "Illumina",
        }

        return result

    def _validate_primary_id(self):
        """Validate primaryId format against regex pattern."""
        pattern = re.compile(settings.PRIMARY_ID_REGEX)
        if not pattern.fullmatch(self.primaryId):
            raise IncorrectlyFormattedPrimaryId(
                f"primaryId:{self.primaryId} incorrectly formatted for genePanel:{self.genePanel}"
            )

    def _validate_libraries(self):
        """Validate that libraries and runs exist when igoComplete is True."""
        if not self.libraries:
            if self.igoComplete:
                raise ErrorInconsistentDataException(
                    f"Sample {self.primaryId} is marked igoComplete but has no libraries"
                )
            else:
                raise MissingDataException(f"Sample {self.primaryId} has no libraries")

        for library in self.libraries:
            if not library.runs:
                if self.igoComplete:
                    raise ErrorInconsistentDataException(
                        f"Sample {self.primaryId} library {library.libraryIgoId} is marked igoComplete but has no runs"
                    )
                else:
                    raise MissingDataException(f"Sample {self.primaryId} library {library.libraryIgoId} has no runs")

    def _validate_required_fields(self):
        """Validate that required fields are not empty."""
        if self.igoComplete is False:
            return
        required_fields = {
            "smileSampleId": self.smileSampleId,
            "smilePatientId": self.smilePatientId,
            "primaryId": self.primaryId,
            "cmoPatientId": self.cmoPatientId,
            "sampleName": self.sampleName,
            "cmoSampleName": self.cmoSampleName,
            "sampleType": self.sampleType,
            "tumorOrNormal": self.tumorOrNormal,
            "sampleClass": self.sampleClass,
            "genePanel": self.genePanel,
            "baitSet": self.baitSet,
        }

        for field_name, field_value in required_fields.items():
            if not field_value or field_value.strip() == "":
                raise MissingDataException(
                    f"Required field '{field_name}' is missing or empty for sample {self.primaryId}"
                )

        # At least one of preservation or sampleOrigin must be present
        preservation_empty = not self.preservation or self.preservation.strip() == ""
        sample_origin_empty = not self.sampleOrigin or self.sampleOrigin.strip() == ""

        if preservation_empty and sample_origin_empty:
            raise MissingDataException(
                f"At least one of 'preservation' or 'sampleOrigin' must be provided for sample {self.primaryId}"
            )

    def is_cmo_sample(self) -> bool:
        """
        Check if this is a CMO sample based on additionalProperties.

        Returns:
            True if this is a CMO sample, False otherwise
        """
        if not self.additionalProperties:
            return False
        return self.additionalProperties.get("isCmoSample", "false").lower() == "true"

    def validate_with_file_checks(self, redelivery: bool = False, log: str = "") -> (str, SampleStatus):
        """
        Comprehensive validation including file permission checks.

        This method orchestrates the validation workflow by delegating to
        specialized validation methods.

        Args:
            redelivery: If True, skip file conflict checks
            log: Existing log string to append to

        Returns:
            Updated log string, SampleError

        Raises:
            ErrorInconsistentDataException: If data is inconsistent
            MissingDataException: If required data is missing
            FailedToCopyFilePermissionDeniedException: If file permissions are bad
        """
        # Check igoComplete first - if false, skip validation
        if not self.igoComplete:
            sample_status = SampleStatus(
                sample_id=self.primaryId,
                igocomplete=self.igoComplete,
                code=None,
                status="SKIP",
                message=f"Sample {self.primaryId} skipped: igoComplete is false",
            )
            log += f"Sample {self.primaryId} skipped: igoComplete is false\n"
            return log, sample_status

        try:
            log = self._validate_primary_id_format(log)
            log = self._validate_libraries_structure(log)
            validation_results = self._validate_all_fastq_files()
            log = self._process_validation_results(validation_results, log, redelivery)
        except Exception as e:
            if isinstance(e, ETLExceptions):
                sample_status = SampleStatus(
                    sample_id=self.primaryId, igocomplete=self.igoComplete, code=e.code, status="FAILED", message=str(e)
                )
            else:
                sample_status = SampleStatus(
                    sample_id=self.primaryId, igocomplete=self.igoComplete, code=None, status="FAILED", message=str(e)
                )
        else:
            sample_status = SampleStatus(
                sample_id=self.primaryId,
                igocomplete=self.igoComplete,
                code=None,
                status="COMPLETED",
                message=f"Sample {self.primaryId}, successfully validated",
            )
            log += f"Sample {self.primaryId}, successfully validated\n"
        return log, sample_status

    def _validate_primary_id_format(self, log: str) -> str:
        """Validate primaryId format against regex pattern."""
        pattern = re.compile(settings.PRIMARY_ID_REGEX)
        if not pattern.fullmatch(self.primaryId):
            error_msg = f"primaryId:{self.primaryId} incorrectly formatted for genePanel:{self.genePanel}"
            logger.error(error_msg)
            log += f"{error_msg}\n"
            raise IncorrectlyFormattedPrimaryId(f"Failed to import, {error_msg}")
        return log

    def _validate_igoComplete(self, log: str) -> str:
        if not self.igoComplete:
            error_msg = f"primaryId:{self.primaryId} is igoComplete:false"

    def _validate_libraries_structure(self, log: str) -> str:
        """Validate that libraries and runs exist."""
        if not self.libraries:
            log += f"Failed to fetch SampleManifest for sampleId:{self.primaryId}. Libraries empty.\n"
            exception_class = ErrorInconsistentDataException if self.igoComplete else MissingDataException
            raise exception_class(f"Failed to fetch SampleManifest for sampleId:{self.primaryId}. Libraries empty.")

        for library in self.libraries:
            if not library.runs:
                error_msg = f"Failed to fetch SampleManifest for sampleId:{self.primaryId}. Runs empty."
                logger.error(error_msg)
                log += f"{error_msg}\n"
                exception_class = ErrorInconsistentDataException if self.igoComplete else MissingDataException
                raise exception_class(error_msg)

        return log

    def _validate_all_fastq_files(self) -> Dict[str, Any]:
        """
        Validate all fastq files across all libraries.

        Returns:
            Dict containing validation results with keys:
                - missing_fastq: bool
                - permission_error: bool
                - conflict: bool
                - failed_runs: List[str]
                - permission_error_files: List[str]
                - conflict_files: List[tuple]
        """
        results = {
            "missing_fastq": False,
            "permission_error": False,
            "conflict": False,
            "failed_runs": [],
            "permission_error_files": [],
            "conflict_files": [],
        }

        for library in self.libraries:
            run_dict = self._convert_runs_to_dict(library.runs)

            for run in run_dict.values():
                self._validate_run_fastqs(run, results)

        return results

    def _validate_run_fastqs(self, run: Run, results: Dict[str, Any]) -> None:
        """
        Validate fastq files for a single run.

        Args:
            run: Run object to validate
            results: Validation results dict to update
        """
        if not run.fastqs:
            logger.error(f"Failed to fetch SampleManifest for sampleId:{self.primaryId}. Fastqs empty.")
            results["missing_fastq"] = True
            run_id = run.runId if run.runId else "None"
            results["failed_runs"].append(run_id)
            return

        for fastq in run.fastqs:
            self._validate_single_fastq(fastq, results)

    def _validate_single_fastq(self, fastq: str, results: Dict[str, Any]) -> None:
        """
        Validate a single fastq file.

        Args:
            fastq: Path to fastq file
            results: Validation results dict to update
        """
        fastq_location = fix_path_iris(fastq)
        try:
            check_file_permissions(fastq_location)
        except FailedToCopyFilePermissionDeniedException:
            results["permission_error"] = True
            results["permission_error_files"].append(fastq)
            return
        try:
            file_search = File.objects.get(original_path=fastq_location, file_group=settings.IMPORT_FILE_GROUP)
            logger.info(f"Processing {fastq}")
            results["conflict"] = True
            results["conflict_files"].append((file_search.path, str(file_search.id)))
        except File.DoesNotExist:
            pass

    def _process_validation_results(self, results: Dict[str, Any], log: str, redelivery: bool) -> str:
        """
        Process validation results and raise appropriate exceptions.

        Args:
            results: Validation results from _validate_all_fastq_files
            log: Current log string
            redelivery: Whether this is a redelivery

        Returns:
            Updated log string

        Raises:
            ErrorInconsistentDataException: If data is inconsistent
            FailedToCopyFilePermissionDeniedException: If file permissions are bad
        """
        # Check for missing fastqs
        if results["missing_fastq"]:
            raise ErrorInconsistentDataException(
                f"Missing fastq data for igocomplete: {self.igoComplete} "
                f"sample {self.primaryId} : {' '.join(results['failed_runs'])}"
            )
        # Check for permission errors
        if results["permission_error"]:
            for fastq in results["permission_error_files"]:
                log += f"Bad permissions {fastq}\n"
            raise FailedToCopyFilePermissionDeniedException(
                f"Failed to access files for sample {self.primaryId} "
                f"{', '.join(results['permission_error_files'])}. Bad permissions"
            )
        # Check for conflicts (only if not redelivery)
        if not redelivery and results["conflict"]:
            for file_path, file_id in results["conflict_files"]:
                log += f"File {file_path} already registered\n"

            res_str = " | ".join(f"{path}: {fid}" for path, fid in results["conflict_files"])
            raise ErrorInconsistentDataException(f"Conflict of fastq file(s): {res_str}")
        return log

    @staticmethod
    def _convert_runs_to_dict(runs: List[Run]) -> Dict[str, Run]:
        """
        Convert list of Run objects to dict keyed by runId.
        Validates that duplicate runs have matching fastq files.
        """
        run_dict = {}
        for run in runs:
            if run.runId not in run_dict:
                run_dict[run.runId] = run
            else:
                # Check if fastqs match for duplicate runs
                if run_dict[run.runId].fastqs:
                    if len(run_dict[run.runId].fastqs) > 0 and len(run.fastqs) > 0:
                        if run_dict[run.runId].fastqs[0] != run.fastqs[0]:
                            logger.error(f"File {run_dict[run.runId].fastqs[0]} does not match with {run.fastqs[0]}")
                            raise FailedToFetchSampleException(
                                f"File {run_dict[run.runId].fastqs[0]} does not match with {run.fastqs[0]}"
                            )
                        if len(run_dict[run.runId].fastqs) > 1 and len(run.fastqs) > 1:
                            if run_dict[run.runId].fastqs[1] != run.fastqs[1]:
                                logger.error(
                                    f"File {run_dict[run.runId].fastqs[1]} does not match with {run.fastqs[1]}"
                                )
                                raise FailedToFetchSampleException(
                                    f"File {run_dict[run.runId].fastqs[1]} does not match with {run.fastqs[1]}"
                                )
                else:
                    logger.error("Fastq empty")
        return run_dict
