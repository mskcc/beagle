# Generated by Django 2.2.28 on 2024-12-24 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0043_auto_20241220_0908"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="filemetadata",
            index=models.Index(fields=["latest"], name="latest_idx"),
        ),
    ]
