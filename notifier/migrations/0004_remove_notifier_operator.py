# Generated by Django 2.2.11 on 2020-08-27 19:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notifier", "0003_jobgroupnotifier_notifier"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notifier",
            name="operator",
        ),
    ]
