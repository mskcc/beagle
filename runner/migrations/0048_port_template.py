# Generated by Django 2.2.13 on 2021-05-27 13:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0047_auto_20210525_1513"),
    ]

    operations = [
        migrations.AddField(
            model_name="port",
            name="template",
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
