import re
import logging
from file_system.repository.file_repository import FileRepository


LOGGER = logging.getLogger(__name__)


def format_sample_name(sample_name, specimen_type, ignore_sample_formatting=False):
    """
    Formats a given sample_name to legacy ROSLIN naming conventions, provided that
    it is in valid CMO Sample Name format (see sample_pattern regex value, below)

    Current format is to prepend sample name with "s_" and convert all hyphens to
    underscores

    If it does not meet sample_pattern requirements OR is not a specimen_type=="CellLine",
    return 'sampleMalFormed'

    ignore_sample_formatting is applied if we want to return a sample name regardless of
    formatting
    """
    sample_pattern = re.compile(r'C-\w{6}-\w{4}-\w')

    if not ignore_sample_formatting:
        try:
            if "s_" in sample_name[:2]:
                return sample_name
            elif bool(sample_pattern.match(sample_name)) or "cellline" in specimen_type.lower():  # cmoSampleName is formatted properly
                sample_name = "s_" + sample_name.replace("-", "_")
                return sample_name
            LOGGER.error('Missing or malformed sampleName: %s', sample_name, exc_info=True)
            return 'sampleNameMalformed'
        except TypeError:
            LOGGER.error(
                "sampleNameError: sampleName is Nonetype; returning 'sampleNameMalformed'."
                )
            return "sampleNameMalformed"
    else:
        return sample_name


def format_patient_id(patient_id):
    return patient_id


def generate_sample_data_content(request_ids):
    # TODO: Move this method to some better place
    result = "SAMPLE_ID\tPATIENT_ID\tCOLLAB_ID\tSAMPLE_TYPE\tGENE_PANEL\tONCOTREE_CODE\tSAMPLE_CLASS\tSPECIMEN_PRESERVATION_TYPE\tSEX\tTISSUE_SITE\tIGO_ID\n"
    ret_str = 'metadata__sampleId'
    if isinstance(request_ids, str):
        request_ids = [request_ids]
    for r in request_ids:
        samples = FileRepository.filter(metadata={"requestId": r}).order_by(ret_str).distinct(
            ret_str).all()
        for sample in samples:
            metadata = sample.metadata
            result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                metadata.get('cmoSampleName', format_sample_name(metadata['sampleName'], metadata['specimenType'])),
                metadata['patientId'],
                metadata['investigatorSampleId'],
                metadata['sampleClass'],
                metadata['recipe'],
                metadata['oncoTreeCode'],
                metadata['specimenType'],
                metadata['preservation'],
                metadata['sex'],
                metadata['tissueLocation'],
                metadata['sampleId']
            )
    return result


def get_r_orientation(fastq_filename):
    """
    Retrieve R orientation of fastq filename
    """
    reversed_filename = ''.join(reversed(fastq_filename))
    r1_idx = reversed_filename.find('1R')
    r2_idx = reversed_filename.find('2R')
    if r1_idx == -1 and r2_idx == -1:
        return "ERROR"
    elif r1_idx > 0 and r2_idx == -1:
        return "R1"
    elif r2_idx > 0 and r1_idx == -1:
        return 'R2'
    elif r1_idx > 0 and r2_idx > 0:
        if r1_idx < r2_idx:
            return 'R1'
        return 'R2'
    return 'ERROR'


def spoof_barcode(sample_file_name, r_orientation):
    """
    Spoof barcode by removing 'R1' or 'R2' from the filename; paired fastqs
    are assumed to have only these two values as different

    We are also assuming there are no periods in the file names other than extensions
    """
    reversed_str = ''.join(reversed(sample_file_name))
    if r_orientation == 'R1':
        reversed_str = reversed_str.replace('1R', '')
    else:
        reversed_str = reversed_str.replace('2R', '')
    reversed_str = ''.join(reversed(reversed_str))
    spoofed_barcode = reversed_str.split(os.extsep)[0]
    return spoofed_barcode


def init_metadata():
    """
    Build a fastq dictionary containing expected metadata for a sample

    This just instantiates it.
    """
    metadata = dict()
    metadata['requestId'] = ""
    metadata['sampleId'] = ""
    metadata['libraryId'] = ""
    metadata['baitSet'] = ""
    metadata['tumorOrNormal'] = ""
    metadata['specimenType'] = ""
    metadata['species'] = ""
    metadata['sampleName'] = ""
    metadata['flowCellId'] = ""
    metadata['barcodeIndex'] = ""
    metadata['patientId'] = ""
    metadata['runDate'] = ""
    metadata['R'] = ""
    metadata['labHeadName'] = ""
    metadata['labHeadEmail'] = ""
    metadata['runId'] = ""
    metadata['preservation'] = ""
    return metadata
