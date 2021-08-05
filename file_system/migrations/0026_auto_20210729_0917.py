# Generated by Django 2.2.24 on 2021-07-29 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0025_auto_20210728_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='patient_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='request',
            name='request_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
