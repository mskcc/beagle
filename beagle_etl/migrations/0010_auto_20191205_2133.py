# Generated by Django 2.2.2 on 2019-12-05 21:33

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0009_auto_20191107_2000"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="callback",
            field=models.CharField(blank=True, default=None, max_length=100),
        ),
        migrations.AlterField(
            model_name="job",
            name="message",
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
