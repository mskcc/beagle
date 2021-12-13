# Generated by Django 2.2.11 on 2020-08-27 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0026_operator_version"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operator",
            name="class_name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="operator",
            name="version",
            field=models.CharField(default=False, max_length=50),
            preserve_default=False,
        ),
    ]
