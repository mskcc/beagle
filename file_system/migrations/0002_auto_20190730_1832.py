# Generated by Django 2.2.2 on 2019-07-30 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="file",
            old_name="cohort",
            new_name="file_group",
        ),
    ]
