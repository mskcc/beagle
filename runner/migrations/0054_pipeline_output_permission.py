# Generated by Django 2.2.28 on 2023-01-05 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0053_auto_20221122_1348"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="output_permission",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
