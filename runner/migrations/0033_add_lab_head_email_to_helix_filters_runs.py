from django.db import migrations
from file_system.repository.file_repository import FileRepository


def add_lab_head_email(apps, _):
    Run = apps.get_model('runner', 'Run')
    files = FileRepository.all()
    helix_pipelines = get_helix_pipelines()

    for helix_pipeline in helix_pipelines:
        helix_runs = Run.objects.filter(app=helix_pipeline.id)
        for run in helix_runs:
            tags = run.tags
            if 'project_prefix' in tags:
                project_prefix = tags['project_prefix']
                metadata = FileRepository.filter(queryset=files, metadata={'requestId': project_prefix}).first().metadata
                if "labHeadEmail" in metadata:
                    tags['labHeadEmail'] = metadata['labHeadEmail']
                    run.tags = tags
                    run.save()


def revert_migration(apps, _):
    Run = apps.get_model('runner', 'Run')
    helix_pipelines = get_helix_pipelines()

    for helix_pipeline in helix_pipelines:
        helix_runs = Run.objects.filter(app=helix_pipeline.id)
        for run in helix_runs:
            run.tags.pop("labHeadEmail", None)
            run.save()


def get_helix_pipelines(apps, _):
    Pipeline = apps.get_model('runner', 'Pipeline')
    Operator = apps.get_model('runner', 'Operator')
    pipelines = Pipeline.objects.all()
    helix_pipelines = []

    for pipeline in pipelines:
        operator_id = pipeline.operator_id
        operator_class_name = Operator.objects.get(id=operator_id).class_name
        if "helix" in operator_class_name.lower():
            helix_pipelines.append(pipeline)
    return helix_pipelines


class Migration(migrations.Migration):
    operations = [
            migrations.RunPython(add_lab_head_email, reverse_code=revert_migration)
    ]
