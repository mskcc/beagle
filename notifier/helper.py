from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.bin.make_sample import format_sample_name


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
