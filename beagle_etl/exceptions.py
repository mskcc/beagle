
class ETLExceptions(Exception):
    code = None


class JobNotFoundExceptions(ETLExceptions):
    code = 100


class FailedToFetchSampleException(ETLExceptions):
    """
    Failed to get response from LIMS or data not in the right format
    """
    code = 101


class MissingDataException(ETLExceptions):
    """
    Sample igoComplete: False, and missing data (partially or completely)
    """
    code = 102


class ErrorInconsistentDataException(ETLExceptions):
    """
    Sample igoComplete: True, and missing data (partially or completely)
    """
    code = 103


class FailedToSubmitToOperatorException(ETLExceptions):
    """
    Unable to find Operator for assay type
    """
    code = 104


class FailedToCalculateChecksum(ETLExceptions):
    """
        Unable to find Operator for assay type
        """
    code = 105


class FailedToFetchPoolNormalException(ETLExceptions):
    """
    Unable to parse and create pool normal file
    """
    code = 106


class FailedToCopyFileException(ETLExceptions):
    """
    Failed to copy File
    """
    code = 107


class FailedToCopyFilePermissionDeniedException(ETLExceptions):
    """
    Failed to copy File PermissionDenied
    """
    code = 108
