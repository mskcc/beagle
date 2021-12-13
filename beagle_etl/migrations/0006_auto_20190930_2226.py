# Generated by Django 2.2.2 on 2019-09-30 22:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0005_auto_20190930_1819"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="jobbasemodel",
            name="basemodel_ptr",
        ),
        migrations.RemoveField(
            model_name="requestfetchjob",
            name="jobbasemodel_ptr",
        ),
        migrations.RemoveField(
            model_name="samplesfetchjob",
            name="jobbasemodel_ptr",
        ),
        migrations.DeleteModel(
            name="ETLError",
        ),
        migrations.DeleteModel(
            name="JobBaseModel",
        ),
        migrations.DeleteModel(
            name="RequestFetchJob",
        ),
        migrations.DeleteModel(
            name="SamplesFetchJob",
        ),
    ]
