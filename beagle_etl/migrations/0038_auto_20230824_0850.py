# Generated by Django 2.2.28 on 2023-08-24 12:50

import beagle_etl.models
from django.db import migrations, models


def fix_status_numbers(apps, _):
    messages = apps.get_model("beagle_etl", "SMILEMessage").objects.all()
    for msg in messages:
        if msg.status >= 1:
            msg.status += 1
            msg.save(update_fields=("status",))


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0037_auto_20230711_1028"),
    ]

    operations = [
        migrations.AlterField(
            model_name="smilemessage",
            name="status",
            field=models.IntegerField(
                choices=[(0, "PENDING"), (2, "COMPLETED"), (3, "NOT_SUPPORTED"), (4, "FAILED")],
                db_index=True,
                default=beagle_etl.models.SmileMessageStatus(0),
            ),
        ),
        migrations.RunPython(fix_status_numbers),
    ]
