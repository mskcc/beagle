# Generated by Django 2.2.28 on 2022-11-08 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0031_auto_20221108_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='filegroup',
            name='default',
            field=models.BooleanField(default=False),
        ),
    ]
