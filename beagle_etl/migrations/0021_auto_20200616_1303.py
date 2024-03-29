# Generated by Django 2.2.10 on 2020-06-16 17:03

from django.db import migrations
from beagle_etl.models import JobStatus


def add_finished_date(apps, _):
    jobs = apps.get_model("beagle_etl", "Job").objects.all()
    for single_job in jobs:
        if single_job.status == JobStatus.COMPLETED or single_job.status == JobStatus.FAILED:
            if not single_job.finished_date:
                single_job.finished_date = single_job.modified_date
                single_job.save()


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0020_auto_20200612_2005"),
    ]

    operations = [migrations.RunPython(add_finished_date)]
