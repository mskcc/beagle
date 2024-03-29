# Generated by Django 2.2.2 on 2019-07-30 16:03

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FileGroup",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=40)),
                ("slug", models.SlugField(unique=True)),
                ("metadata", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Sample",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("sample_name", models.CharField(max_length=40)),
                ("tags", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Storage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=20)),
                ("type", models.IntegerField(choices=[(0, "LOCAL"), (1, "AWS_S3")])),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SampleMetadata",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("version", models.IntegerField()),
                ("metadata", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ("sample", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="file_system.Sample")),
                (
                    "user",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FileGroupMetadata",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("version", models.IntegerField()),
                ("metadata", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ("cohort", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="file_system.FileGroup")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="filegroup",
            name="storage",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="file_system.Storage"
            ),
        ),
        migrations.CreateModel(
            name="File",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("file_name", models.CharField(max_length=100)),
                ("path", models.CharField(max_length=400)),
                ("size", models.BigIntegerField()),
                ("cohort", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="file_system.FileGroup")),
                (
                    "sample",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="file_system.Sample"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
