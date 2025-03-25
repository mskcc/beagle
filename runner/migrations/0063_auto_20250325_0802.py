# Generated by Django 2.2.28 on 2025-03-25 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0062_pipeline_nfcore_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="log_directory",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="log_prefix",
            field=models.CharField(default="", max_length=30),
        ),
    ]
