# Generated by Django 2.2.13 on 2021-01-12 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0040_auto_20201221_1655"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="started",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="submitted",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
