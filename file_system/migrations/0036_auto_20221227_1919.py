# Generated by Django 2.2.28 on 2022-12-28 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0035_remove_request_lab_head_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="sample",
            name="cas_qc_notes",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="sample",
            name="igo_qc_notes",
            field=models.TextField(default=""),
        ),
    ]
