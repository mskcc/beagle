# Generated by Django 2.2.13 on 2021-03-16 19:57

from django.db import migrations, models
import runner.models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0043_run_run_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='run_type',
            field=models.IntegerField(choices=[(0, 'CWL'), (1, 'NEXTFLOW')], db_index=True, default=runner.models.RunType(0)),
        ),
    ]
