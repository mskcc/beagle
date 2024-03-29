# Generated by Django 2.2.24 on 2022-04-14 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0029_operator_notifier"),
    ]

    operations = [
        migrations.CreateModel(
            name="SMILEMessage",
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
                ("topic", models.CharField(max_length=1000)),
                ("request_id", models.CharField(max_length=100)),
                ("message", models.TextField()),
            ],
            bases=("beagle_etl.basemodel",),
        ),
    ]
