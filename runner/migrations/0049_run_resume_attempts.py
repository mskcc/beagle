# Generated by Django 2.2.20 on 2021-12-07 16:21

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
