# Generated by Django 2.2.11 on 2020-12-01 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0023_auto_20201117_1729"),
        ("runner", "0035_run_resume"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="samples",
            field=models.ManyToManyField(to="file_system.Sample"),
        ),
    ]
