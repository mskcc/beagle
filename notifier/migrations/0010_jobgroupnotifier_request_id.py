# Generated by Django 2.2.24 on 2021-09-10 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifier', '0009_auto_20210908_0606'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobgroupnotifier',
            name='request_id',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
