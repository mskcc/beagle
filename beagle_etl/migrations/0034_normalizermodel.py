# Generated by Django 2.2.24 on 2022-05-23 11:18

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0033_requestcallbackjob"),
    ]

    operations = [
        migrations.CreateModel(
            name="NormalizerModel",
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
                ("condition", django.contrib.postgres.fields.jsonb.JSONField()),
                ("normalizer", django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            bases=("beagle_etl.basemodel",),
        ),
    ]
