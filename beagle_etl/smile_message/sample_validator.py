import re
import logging
from django.conf import settings
from beagle_etl.exceptions import (
    ErrorInconsistentDataException,
    MissingDataException,
    FailedToCopyFilePermissionDeniedException,
    IncorrectlyFormattedPrimaryId,
    FailedToCopyFilePermissionDeniedException,
    FailedToCopyFileException,
    FailedToFetchSampleException,
    IncorrectlyFormattedPrimaryId,
)
from file_system.models import File
from beagle_etl.jobs.helper_jobs import check_file_permissions, fix_path_iris


logger = logging.getLogger(__name__)


class SampleValidator(object):


    @staticmethod
    def validate_sample(sample_id, libraries, igocomplete, gene_panel, log="", redelivery=False):
        conflict = False
        missing_fastq = False
        permission_error = False
        permission_error_files = []
        failed_runs = []
        conflict_files = []

        pattern = re.compile(settings.PRIMARY_ID_REGEX)
        if not pattern.fullmatch(sample_id):
            logger.error(f"primaryId:{sample_id} incorrectly formatted for genePanel:{gene_panel}")
            log += f"primaryId:{sample_id} incorrectly formatted for genePanel:{gene_panel}\n"
            raise IncorrectlyFormattedPrimaryId(
                f"Failed to import, primaryId:{sample_id} incorrectly formatted for genePanel:{gene_panel}"
            )

        if not libraries:
            log += f"Failed to fetch SampleManifest for sampleId:{sample_id}. Libraries empty.\n"
            if igocomplete:
                raise ErrorInconsistentDataException(
                    f"Failed to fetch SampleManifest for sampleId:{sample_id}. Libraries empty."
                )
            else:
                raise MissingDataException(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Libraries empty.")

        for library in libraries:
            runs = library.get("runs")
            if not runs:
                logger.error(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty.")
                log += f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty.\n"
                if igocomplete:
                    raise ErrorInconsistentDataException(
                        f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty."
                    )
                else:
                    raise MissingDataException(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Runs empty.")

            run_dict = SampleValidator.convert_to_dict(runs)

            for run in run_dict.values():
                fastqs = run.get("fastqs")
                if not fastqs:
                    logger.error(f"Failed to fetch SampleManifest for sampleId:{sample_id}. Fastqs empty.")
                    log += f"Failed to fetch SampleManifest for sampleId:{sample_id}. Fastqs empty.\n"
                    missing_fastq = True
                    run_id = run["runId"] if run["runId"] else "None"
                    failed_runs.append(run_id)
                    continue
                else:
                    if not redelivery:
                        for fastq in fastqs:
                            fastq_location = fix_path_iris(fastq)
                            try:
                                # Check File Permissions
                                check_file_permissions(fastq_location)
                            except FailedToCopyFilePermissionDeniedException as e:
                                permission_error = True
                                permission_error_files.append(fastq)
                                log += f"Bad permissions {fastq}\n"
                                continue
                            # Check is file already registered
                            try:
                                file_search = File.objects.get(path=fastq_location, file_group=settings.IMPORT_FILE_GROUP)
                            except File.DoesNotExist:
                                continue

                            logger.info("Processing %s" % fastq)
                            if file_search:
                                log += f"File {fastq} already registered\n"
                                conflict = True
                                conflict_files.append((file_search.path, str(file_search.id)))
        if missing_fastq:
            raise ErrorInconsistentDataException(
                f"Missing fastq data for igcomplete: {igocomplete} sample {sample_id} : {' '.join(failed_runs)}"
            )
        if permission_error:
            raise FailedToCopyFilePermissionDeniedException(
                f"Failed to access files for sample {sample_id} {', '.join(permission_error_files)}. Bad permissions"
            )
        if not redelivery:
            if conflict:
                res_str = ""
                for f in conflict_files:
                    res_str += "%s: %s" % (f[0], f[1])
                raise ErrorInconsistentDataException(f"Conflict of fastq file(s) {res_str}")


    @staticmethod
    def convert_to_dict(runs):
        run_dict = dict()
        for run in runs:
            if not run_dict.get(run["runId"]):
                run_dict[run["runId"]] = run
            else:
                if run_dict[run["runId"]].get("fastqs"):
                    logger.error("Fastq empty")
                    if run_dict[run["runId"]]["fastqs"][0] != run["fastqs"][0]:
                        logger.error(
                            "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][0], run["fastqs"][0])
                        )
                        raise FailedToFetchSampleException(
                            "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][0], run["fastqs"][0])
                        )
                    if run_dict[run["runId"]]["fastqs"][1] != run["fastqs"][1]:
                        logger.error(
                            "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][1], run["fastqs"][1])
                        )
                        raise FailedToFetchSampleException(
                            "File %s do not match with %s" % (run_dict[run["runId"]]["fastqs"][1], run["fastqs"][1])
                        )
        return run_dict
