# Generated by Django 2.2.28 on 2023-06-08 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("study", "0002_jobgroupwatcher_jobgroupwatcherconfig"),
    ]

    operations = [
        migrations.AlterField(
            model_name="study",
            name="study_id",
            field=models.CharField(max_length=40, unique=True),
        ),
    ]
