# Generated by Django 2.2.24 on 2021-08-31 12:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifier', '0005_auto_20201116_1419'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobgroup',
            name='jira_id',
        ),
    ]