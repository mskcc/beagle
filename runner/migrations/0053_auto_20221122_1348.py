# Generated by Django 2.2.28 on 2022-11-22 18:48

from django.db import migrations, models
import runner.models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0052_remove_run_log_directory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operatorrun",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "CREATING"),
                    (1, "READY"),
                    (2, "RUNNING"),
                    (3, "FAILED"),
                    (4, "COMPLETED"),
                    (5, "TERMINATED"),
                ],
                db_index=True,
                default=runner.models.RunStatus(0),
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "CREATING"),
                    (1, "READY"),
                    (2, "RUNNING"),
                    (3, "FAILED"),
                    (4, "COMPLETED"),
                    (5, "TERMINATED"),
                ],
                db_index=True,
            ),
        ),
    ]
