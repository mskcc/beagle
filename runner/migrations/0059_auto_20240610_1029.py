# Generated by Django 2.2.28 on 2024-06-10 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0058_auto_20240501_0133"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="output_gid",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="output_uid",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
