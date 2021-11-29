# Generated by Django 2.2.9 on 2020-05-09 06:31

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0026_remove_operatorrun_trigger"),
    ]

    operations = [
        migrations.AddField(
            model_name="port",
            name="notify",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="run",
            name="notify_for_outputs",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(blank=True, max_length=40), default=[], size=None
            ),
            preserve_default=False,
        ),
    ]
