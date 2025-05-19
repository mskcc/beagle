from django.db.models import Q
from django.conf import settings
from file_system.repository.file_repository import FileRepository
from beagle_etl.metadata.validator import MetadataValidator
from runner.operator.helper import format_sample_name


def get_project_id(request_id):
    return request_id.split("_")[0]


def get_gene_panel(request_id):
    return FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.RECIPE_METADATA_KEY
    ).first()


def get_samples(request_id):
    return FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.SAMPLE_ID_METADATA_KEY
    ).all()


def get_number_of_tumor_samples(request_id):
    return FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id, settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor"},
        values_metadata=settings.SAMPLE_ID_METADATA_KEY,
    ).count()


def get_emails_to_notify(request_id, notification_type=None):
    investigator_email = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id},
        values_metadata=settings.INVESTIGATOR_EMAIL_METADATA_KEY,
    ).first()
    lab_head_email = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request_id}, values_metadata=settings.LAB_HEAD_EMAIL_METADATA_KEY
    ).first()
    send_to = settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO
    if notification_type in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_NOTIFY_EXTERNAL:
        if investigator_email not in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_BLACKLIST and investigator_email:
            send_to.append(investigator_email)
        if lab_head_email not in settings.BEAGLE_NOTIFIER_VOYAGER_STATUS_BLACKLIST and lab_head_email:
            send_to.append(lab_head_email)
    return list(set(send_to))


def generate_sample_data_content(files, pipeline_name, pipeline_github, pipeline_version, dmp_samples=None):
    result = "SAMPLE_ID\tREQUEST_ID\tPROJECT_ID\tPATIENT_ID\tCOLLAB_ID\tSAMPLE_TYPE\tGENE_PANEL\tONCOTREE_CODE\tSAMPLE_CLASS\tSPECIMEN_PRESERVATION_TYPE\tSEX\tTISSUE_SITE\tIGO_ID\tRUN_MODE\tPIPELINE\tPIPELINE_GITHUB_LINK\tPIPELINE_VERSION\n"
    ret_str = "metadata__{sample_id_key}".format(sample_id_key=settings.SAMPLE_ID_METADATA_KEY)
    query = Q(file__file_group_id=settings.IMPORT_FILE_GROUP)
    query |= Q(file__file_group__slug="origin-unknown")
    query |= Q(file__file_group__slug="fero-legacy-data")
    query = query & Q(file__path__in=files)
    samples = FileRepository.filter(q=query).order_by(ret_str).distinct(ret_str).all()
    for sample in samples:
        metadata = sample.metadata
        result += generate_sample_data_content_str(metadata, pipeline_name, pipeline_github, pipeline_version)
    if dmp_samples:
        for sample in dmp_samples:
            metadata = sample[0].metadata
            project_id = metadata[settings.REQUEST_ID_METADATA_KEY]
            result += generate_sample_data_content_str(
                metadata, pipeline_name, pipeline_github, pipeline_version, project_id
            )
    return result


def generate_sample_data_content_str(metadata, pipeline_name, pipeline_github, pipeline_version, project_id=None):
    if project_id:
        project_id = get_project_id(metadata[settings.REQUEST_ID_METADATA_KEY])
    sample_id = metadata.get(
        settings.CMO_SAMPLE_TAG_METADATA_KEY,
        format_sample_name(
            metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY], metadata[settings.SAMPLE_CLASS_METADATA_KEY]
        ),
    )
    result = f"{sample_id}\t{metadata[settings.REQUEST_ID_METADATA_KEY]}\t{project_id}\t{metadata[settings.PATIENT_ID_METADATA_KEY]}\t{metadata['investigatorSampleId']}\t{MetadataValidator.clean_value(metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY])}\t{gene_panel_mapping(MetadataValidator.clean_value(metadata[settings.RECIPE_METADATA_KEY]), MetadataValidator.clean_value(metadata[settings.BAITSET_METADATA_KEY]))}\t{MetadataValidator.clean_value(metadata[settings.ONCOTREE_METADATA_KEY])}\t{MetadataValidator.clean_value(metadata[settings.SAMPLE_CLASS_METADATA_KEY])}\t{MetadataValidator.clean_value(metadata['preservation'])}\t{MetadataValidator.clean_value(metadata['sex'])}\t{MetadataValidator.clean_value(metadata['tissueLocation'])}\t{metadata[settings.SAMPLE_ID_METADATA_KEY]}\t{MetadataValidator.clean_value(metadata['runMode'])}\t{pipeline_name}\t{pipeline_github}\t{pipeline_version}\n"
    return result


def gene_panel_mapping(gene_panel, bait_set):
    return settings.GENE_PANEL_TABLE.get(gene_panel, {}).get(bait_set, "ERROR")
