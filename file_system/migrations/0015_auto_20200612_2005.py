# Generated by Django 2.2.10 on 2020-06-13 00:05

import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0014_file_checksum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='filegroup',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='filegroupmetadata',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='filemetadata',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='filerunmap',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='storage',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AddIndex(
            model_name='filemetadata',
            index=models.Index(fields=['version'], name='version_idx'),
        ),
        migrations.AddIndex(
            model_name='filemetadata',
            index=django.contrib.postgres.indexes.GinIndex(fields=['metadata'], name='metadata_gin'),
        ),
    ]
