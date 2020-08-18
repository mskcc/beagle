from django.db import migrations
from file_system.repository.file_repository import FileRepository


def add_lab_head_email(apps, _):
    Run = apps.get_model('runner', 'Run')
    FileMetadata = apps.get_model('file_system', 'FileMetadata')
    helix_pipelines = get_helix_pipelines(apps)
    for helix_pipeline in helix_pipelines:
        helix_runs = Run.objects.filter(app=helix_pipeline.id)
        for run in helix_runs:
            tags = run.tags
            if 'project_prefix' in tags:
                project_prefix = tags['project_prefix']
                metadata = FileMetadata.objects.filter(metadata__requestId=project_prefix).first()
                if metadata:
                    labHeadEmail = metadata.metadata.get('labHeadEmail')
                    if labHeadEmail:
                        tags['labHeadEmail'] = labHeadEmail
                        run.tags = tags
                        run.save()


def revert_migration(apps, _):
    Run = apps.get_model('runner', 'Run')
    helix_pipelines = get_helix_pipelines(apps)

    for helix_pipeline in helix_pipelines:
        helix_runs = Run.objects.filter(app=helix_pipeline.id)
        for run in helix_runs:
            run.tags.pop("labHeadEmail", None)
            run.save()


def get_helix_pipelines(apps):
    Pipeline = apps.get_model('runner', 'Pipeline')
    Operator = apps.get_model('beagle_etl', 'Operator')
    pipelines = Pipeline.objects.all()
    helix_pipelines = []

    for pipeline in pipelines:
        operator_id = pipeline.operator_id
        operator_class_name = Operator.objects.get(id=operator_id).class_name
        if "helix" in operator_class_name.lower():
            helix_pipelines.append(pipeline)
    return helix_pipelines


class Migration(migrations.Migration):

    dependencies = [
            ('runner', '0032_auto_20200805_0153'),
            ]

    operations = [
            migrations.RunPython(add_lab_head_email, reverse_code=revert_migration)
    ]
