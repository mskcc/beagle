# Generated by Django 2.2.28 on 2024-09-26 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0061_auto_20240820_1837"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="nfcore_template",
            field=models.BooleanField(default=False),
        ),
    ]
