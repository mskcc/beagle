# Generated by Django 2.2.2 on 2019-11-07 19:57

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0008_auto_20191106_1920"),
    ]

    operations = [
        migrations.CreateModel(
            name="FileRunMap",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("run", django.contrib.postgres.fields.jsonb.JSONField(default=list)),
                ("file", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="file_system.File")),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
