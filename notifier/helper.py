from django.db.models import Q
from django.conf import settings
from file_system.repository.file_repository import FileRepository
from runner.operator.argos_operator.bin.make_sample import format_sample_name


def get_project_id(request_id):
    return request_id.split('_')[0]


def generate_sample_data_content(files, pipeline_name, pipeline_github, pipeline_version):
    result = "SAMPLE_ID\tREQUEST_ID\tPROJECT_ID\tPATIENT_ID\tCOLLAB_ID\tSAMPLE_TYPE\tGENE_PANEL\tONCOTREE_CODE\tSAMPLE_CLASS\tSPECIMEN_PRESERVATION_TYPE\tSEX\tTISSUE_SITE\tIGO_ID\tPIPELINE_NAME\tPIPELINE_GITHUB_LINK\tPIPELINE_VERSION\n"
    ret_str = 'metadata__sampleId'
    query = Q(file__path__in=files) & Q(file__file_group_id=settings.IMPORT_FILE_GROUP)
    samples = FileRepository.filter(q=query).order_by(ret_str).distinct(ret_str).all()
    for sample in samples:
        metadata = sample.metadata
        result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            metadata.get('cmoSampleName', format_sample_name(metadata['sampleName'], metadata['specimenType'])),
            metadata['requestId'],
            get_project_id(metadata['requestId']),
            metadata['patientId'],
            metadata['investigatorSampleId'],
            metadata['sampleClass'],
            metadata['recipe'],
            metadata['oncoTreeCode'],
            metadata['specimenType'],
            metadata['preservation'],
            metadata['sex'],
            metadata['tissueLocation'],
            metadata['sampleId'],
            pipeline_name,
            pipeline_github,
            pipeline_version,
        )
    return result
