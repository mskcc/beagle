# Generated by Django 2.2.28 on 2023-03-23 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file_system', '0036_auto_20221227_1919'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='lab_head_email',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
