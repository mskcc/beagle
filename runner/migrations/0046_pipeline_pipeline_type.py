# Generated by Django 2.2.13 on 2021-05-25 19:11

from django.db import migrations, models
import runner.models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0045_merge_20210407_0859'),
    ]

    operations = [
        migrations.AddField(
            model_name='pipeline',
            name='pipeline_type',
            field=models.IntegerField(choices=[(0, 'CWL'), (1, 'NEXTFLOW')], db_index=True, default=runner.models.ProtocolType(0)),
        ),
    ]