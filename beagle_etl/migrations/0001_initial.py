# Generated by Django 2.2.2 on 2019-09-24 22:38

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BaseModel",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ETLError",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_id", models.UUIDField()),
                ("error", django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="JobBaseModel",
            fields=[
                (
                    "basemodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="beagle_etl.BaseModel",
                    ),
                ),
                ("status", models.IntegerField(choices=[(0, "CREATED"), (1, "PROCESSED"), (2, "FAILED")])),
            ],
            bases=("beagle_etl.basemodel",),
        ),
        migrations.CreateModel(
            name="RequestFetchJob",
            fields=[
                (
                    "jobbasemodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="beagle_etl.JobBaseModel",
                    ),
                ),
                ("request_id", models.CharField(max_length=40)),
                ("data", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            bases=("beagle_etl.jobbasemodel",),
        ),
        migrations.CreateModel(
            name="SamplesFetchJob",
            fields=[
                (
                    "jobbasemodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="beagle_etl.JobBaseModel",
                    ),
                ),
                ("sample_id", models.CharField(max_length=40)),
                ("data", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            bases=("beagle_etl.jobbasemodel",),
        ),
    ]
