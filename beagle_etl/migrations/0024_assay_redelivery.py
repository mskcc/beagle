# Generated by Django 2.2.11 on 2020-08-12 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beagle_etl', '0023_job_job_group_notifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='assay',
            name='redelivery',
            field=models.BooleanField(default=True),
        ),
    ]
