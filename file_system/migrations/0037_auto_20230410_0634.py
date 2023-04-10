# Generated by Django 2.2.28 on 2023-04-10 06:34

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0036_auto_20221227_1919'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='file',
            name='request',
        ),
        migrations.AddField(
            model_name='file',
            name='patient_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='request_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='file',
            name='samples',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), default=list, size=None),
        ),
        migrations.AddField(
            model_name='patient',
            name='samples',
            field=models.ManyToManyField(related_name='patient_samples', to='file_system.Sample'),
        ),
        migrations.AddField(
            model_name='sample',
            name='request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='file_system.Request'),
        ),
    ]
