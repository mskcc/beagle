from django.db.models import Q
from django.conf import settings
from file_system.repository.file_repository import FileRepository
from file_system.metadata.validator import MetadataValidator
from runner.operator.helper import format_sample_name


def get_project_id(request_id):
    return request_id.split('_')[0]


def generate_sample_data_content(files, pipeline_name, pipeline_github, pipeline_version):
    result = "SAMPLE_ID\tREQUEST_ID\tPROJECT_ID\tPATIENT_ID\tCOLLAB_ID\tSAMPLE_TYPE\tGENE_PANEL\tONCOTREE_CODE\tSAMPLE_CLASS\tSPECIMEN_PRESERVATION_TYPE\tSEX\tTISSUE_SITE\tIGO_ID\tRUN_MODE\tPIPELINE\tPIPELINE_GITHUB_LINK\tPIPELINE_VERSION\n"
    ret_str = 'metadata__sampleId'
    query = Q(file__file_group_id=settings.IMPORT_FILE_GROUP)
    query |= Q(file__file_group__slug="origin-unknown")
    query = query & Q(file__path__in=files)
    samples = FileRepository.filter(q=query).order_by(ret_str).distinct(ret_str).all()
    for sample in samples:
        metadata = sample.metadata
        result += '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(
            metadata.get('cmoSampleName', format_sample_name(metadata['sampleName'], metadata['specimenType'])),
            metadata['requestId'],
            get_project_id(metadata['requestId']),
            metadata['patientId'],
            metadata['investigatorSampleId'],
            MetadataValidator.clean_value(metadata['sampleClass']),
            MetadataValidator.clean_value(metadata['recipe']),
            MetadataValidator.clean_value(metadata['oncoTreeCode']),
            MetadataValidator.clean_value(metadata['specimenType']),
            MetadataValidator.clean_value(metadata['preservation']),
            MetadataValidator.clean_value(metadata['sex']),
            MetadataValidator.clean_value(metadata['tissueLocation']),
            metadata['sampleId'],
            MetadataValidator.clean_value(metadata['runMode']),
            pipeline_name,
            pipeline_github,
            pipeline_version,
        )
    return result


def generate_json_manifest(request_id):
    files = FileRepository.objects.all()
    q = Q(metadata__requestId=request_id)
    q_fg = Q(file__file_group_id=settings.IMPORT_FILE_GROUP)
    q_fg |= Q(file__file_group__slug="origin-unknown")
    ret_str = 'metadata__sampleId'
    query = q & q_fg & Q(file__path__in=files)
    samples = FileRepository.filter(q=query).order_by(ret_str).distinct(ret_str).all()
    request_data = request_keys()
    samples_list = list()
    for sample in samples:
        metadata = sample.metadata
        for key in request_data:
            if not request_data[key]: # if request_data[key] hasn't been filled yet
                request_data[key] = get_data(metadata, key)
        sample_data = sample_keys()
        for key in sample_data:
            if key in metadata:
                sample_data[key] = get_data(metadata, key)
        samples_list.append(sample_data)
    data = dict()
    data['request'] = request_data
    data['samples'] = samples_list
    return data


def get_data(metadata, k):
    if k in metadata:
        return MetadataValidator.clean_value(metadata[k])
    return ''


def sample_keys():
    keys = [ 'cmoSampleName', 'patientId', 'investigatorSampleId', 'sampleClass',
            'oncoTreeCode', 'specimenType', 'preservation', 'sex', 'tissueLocation',
            'sampleId', 'runMode' ]
    r = dict()
    for key in keys:
        r[key] = ""
    return r


def request_keys():
    keys = [ 'dataAnalystEmail', 'dataAccessEmails', 'dataAnalystName',
            'investigatorEmail', 'labHeadEmail', 'labHeadName', 'libraryType',
            'otherContactEmails', 'piEmail', 'recipe', 'projectManagerName',
            'qcAccessEmails', 'investigatorName' ]

    r = dict()
    for key in keys:
        r[key] = ''
    return r
