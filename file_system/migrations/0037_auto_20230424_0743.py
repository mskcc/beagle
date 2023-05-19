# Generated by Django 2.2.28 on 2023-04-24 11:43

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0036_auto_20221227_1919"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="file",
            name="patient",
        ),
        migrations.RemoveField(
            model_name="file",
            name="request",
        ),
        migrations.AddField(
            model_name="file",
            name="patient_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="file",
            name="request_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="file",
            name="samples",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="samples",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100), default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="request",
            name="lab_head_email",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="sample",
            name="request_id",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
