from django.db.models import Q
from django.conf import settings
from file_system.repository.file_repository import FileRepository
from file_system.metadata.validator import MetadataValidator
from runner.operator.helper import format_sample_name


def get_project_id(request_id):
    return request_id.split('_')[0]


def generate_sample_data_content(files, pipeline_name, pipeline_github, pipeline_version):
    result = "SAMPLE_ID\tREQUEST_ID\tPROJECT_ID\tPATIENT_ID\tCOLLAB_ID\tSAMPLE_TYPE\tGENE_PANEL\tONCOTREE_CODE\tSAMPLE_CLASS\tSPECIMEN_PRESERVATION_TYPE\tSEX\tTISSUE_SITE\tIGO_ID\tRUN_MODE\tPIPELINE\tPIPELINE_GITHUB_LINK\tPIPELINE_VERSION\n"
    ret_str = 'metadata__{sample_id_key}'.format(sample_id_key=settings.SAMPLE_ID_METADATA_KEY)
    query = Q(file__file_group_id=settings.IMPORT_FILE_GROUP)
    query |= Q(file__file_group__slug="origin-unknown")
    query |= Q(file__file_group__slug="fero-legacy-data") 
    query = query & Q(file__path__in=files)
    samples = FileRepository.filter(q=query).order_by(ret_str).distinct(ret_str).all()
    for sample in samples:
        metadata = sample.metadata
        result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            metadata.get(settings.CMO_SAMPLE_TAG_METADATA_KEY, format_sample_name(metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY], metadata[settings.SAMPLE_CLASS_METADATA_KEY])),
            metadata[settings.REQUEST_ID_METADATA_KEY],
            get_project_id(metadata[settings.REQUEST_ID_METADATA_KEY]),
            metadata['patientId'],
            metadata['investigatorSampleId'],
            MetadataValidator.clean_value(metadata[settings.SAMPLE_CLASS_METADATA_KEY]),
            MetadataValidator.clean_value(metadata[settings.RECIPE_METADATA_KEY]),
            MetadataValidator.clean_value(metadata['oncoTreeCode']),
            MetadataValidator.clean_value(metadata[settings.SAMPLE_CLASS_METADATA_KEY]),
            MetadataValidator.clean_value(metadata['preservation']),
            MetadataValidator.clean_value(metadata['sex']),
            MetadataValidator.clean_value(metadata['tissueLocation']),
            metadata[settings.SAMPLE_ID_METADATA_KEY],
            MetadataValidator.clean_value(metadata['runMode']),
            pipeline_name,
            pipeline_github,
            pipeline_version,
        )
    return result
