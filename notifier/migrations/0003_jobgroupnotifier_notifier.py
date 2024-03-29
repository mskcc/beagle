# Generated by Django 2.2.11 on 2020-08-03 20:28

from django.db import migrations, models
import django.db.models.deletion


def move_jira_id(apps, _):
    Notifier = apps.get_model("notifier", "Notifier")

    import_notifier = Notifier.objects.create(default=True, notifier_type="JIRA", board="VADEV", operator=None)

    JobGroup = apps.get_model("notifier", "JobGroup")
    JobGroupNotifier = apps.get_model("notifier", "JobGroupNotifier")

    job_groups = JobGroup.objects.all()
    for job_group in job_groups:
        JobGroupNotifier.objects.create(job_group=job_group, jira_id=job_group.jira_id, notifier_type=import_notifier)


def revert_move_jira_id(apps, _):
    JobGroupNotifier = apps.get_model("notifier", "JobGroupNotifier")
    JobGroupNotifier.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0022_remove_failed_jobs"),
        ("notifier", "0002_auto_20200612_2005"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notifier",
            fields=[
                (
                    "basemodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="notifier.BaseModel",
                    ),
                ),
                ("default", models.BooleanField(default=False)),
                ("notifier_type", models.CharField(max_length=100)),
                ("board", models.CharField(max_length=20)),
                (
                    "operator",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="beagle_etl.Operator"
                    ),
                ),
            ],
            bases=("notifier.basemodel",),
        ),
        migrations.CreateModel(
            name="JobGroupNotifier",
            fields=[
                (
                    "basemodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="notifier.BaseModel",
                    ),
                ),
                ("jira_id", models.CharField(blank=True, max_length=20, null=True)),
                ("job_group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="notifier.JobGroup")),
                (
                    "notifier_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="notifier.Notifier"),
                ),
            ],
            bases=("notifier.basemodel",),
        ),
        migrations.RunPython(move_jira_id),
    ]
