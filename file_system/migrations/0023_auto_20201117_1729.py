# Generated by Django 2.2.11 on 2020-11-17 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0022_filemetadata_latest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='sample_id',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
