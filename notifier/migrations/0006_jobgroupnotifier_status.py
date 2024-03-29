# Generated by Django 2.2.24 on 2021-09-07 16:51

from django.db import migrations, models
import notifier.models


class Migration(migrations.Migration):

    dependencies = [
        ("notifier", "0005_auto_20201116_1419"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobgroupnotifier",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "IN_VOYAGER"),
                    (1, "NOT_FOR_CI"),
                    (2, "CANT_DO"),
                    (3, "TERMINAL_DELIVER_AS_IS"),
                    (4, "PARTIAL_DELIVERY_WILL_RERUN_REMAINING"),
                    (5, "DELIVER_AS_IS_WILL_NOT_RERUN"),
                    (6, "NO_DELIVERY_WILL_REEXECUTE"),
                    (7, "PRIMARY_OUTPUT_DELIVERY"),
                    (8, "DONE"),
                    (9, "CI_REVIEW_NEEDED"),
                    (10, "INCOMPLETE_REQUEST"),
                    (11, "PM_HOLD"),
                    (12, "MISSING_INFORMATION"),
                    (13, "SOMEDAY_MAYBE"),
                    (14, "PIPELINE_COMPLETED_NO_FAILURES"),
                    (15, "WAITING_FOR_PORTAL"),
                    (16, "READY_FOR_STANDARD_DELIVERY"),
                    (17, "READY_FOR_CUSTOM_DELIVERY"),
                    (18, "UNKNOWN"),
                ],
                default=notifier.models.JiraStatus(18),
            ),
        ),
    ]
