# Generated by Django 2.2.13 on 2021-03-16 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0042_populate_job_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='run_type',
            field=models.IntegerField(choices=[(0, 'CWL'), (1, 'NEXTFLOW')], db_index=True, default=0),
            preserve_default=False,
        ),
    ]