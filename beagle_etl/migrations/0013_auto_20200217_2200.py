# Generated by Django 2.2.9 on 2020-02-17 22:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0012_operator_class_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operator",
            name="slug",
            field=models.CharField(default=False, max_length=100),
        ),
    ]
