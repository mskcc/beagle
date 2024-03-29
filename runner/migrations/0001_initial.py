# Generated by Django 2.2.2 on 2019-08-27 20:21

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Pipeline",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("github", models.CharField(max_length=300)),
                ("version", models.CharField(max_length=100)),
                ("entrypoint", models.CharField(max_length=100)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Run",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(0, "CREATING"), (1, "READY"), (2, "RUNNING"), (3, "FAILED"), (4, "COMPLETED")]
                    ),
                ),
                ("job_statuses", django.contrib.postgres.fields.jsonb.JSONField()),
                (
                    "app",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="runner.Pipeline"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Port",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("port_type", models.IntegerField(choices=[(0, "INPUT"), (1, "OUTPUT")])),
                ("schema", django.contrib.postgres.fields.jsonb.JSONField()),
                ("value", django.contrib.postgres.fields.jsonb.JSONField()),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="runner.Run")),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
