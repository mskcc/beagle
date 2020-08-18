from django.db import migrations


def add_lab_head_email(apps, _):
    Run = apps.get_model('runner', 'Run')
    FileMetadata = apps.get_model('file_system', 'FileMetadata')
    helix_runs = Run.objects.filter(app__name__contains='helix')
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
    helix_runs = Run.objects.filter(app__name__contains='helix')
    for run in helix_runs:
        run.tags.pop("labHeadEmail", None)
        run.save()


class Migration(migrations.Migration):

    dependencies = [
            ('runner', '0032_auto_20200805_0153'),
            ]

    operations = [
            migrations.RunPython(add_lab_head_email, reverse_code=revert_migration)
    ]
