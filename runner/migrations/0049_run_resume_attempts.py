# Generated by Django 2.2.24 on 2021-11-29 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0048_port_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='resume_attempts',
            field=models.IntegerField(default=5),
        ),
    ]
