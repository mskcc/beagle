# Generated by Django 2.2.2 on 2019-08-20 15:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0006_auto_20190819_1621"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="filegroup",
            name="metadata",
        ),
    ]
