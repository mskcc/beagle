import uuid
import django.db.models.deletion
import runner.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifier", "0015_auto_20240703_1411"),
        ("operator_manager", "0002_migrate_beagle_etl_operators"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperatorRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "CREATING"),
                            (1, "READY"),
                            (2, "RUNNING"),
                            (3, "FAILED"),
                            (4, "COMPLETED"),
                            (5, "TERMINATED"),
                        ],
                        db_index=True,
                        default=runner.models.RunStatus["CREATING"],
                    ),
                ),
                ("num_total_runs", models.IntegerField()),
                ("num_manual_restarts", models.IntegerField(default=0)),
                ("triggered_alert", models.BooleanField(default=False)),
                ("num_completed_runs", models.IntegerField(default=0)),
                ("num_failed_runs", models.IntegerField(default=0)),
                ("finished_date", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "job_group",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="notifier.jobgroup"
                    ),
                ),
                (
                    "job_group_notifier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="notifier.jobgroupnotifier",
                    ),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to="operator_manager.operator"
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="operator_manager.operatorrun",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="OperatorTrigger",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid1, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                (
                    "aggregate_condition",
                    models.IntegerField(choices=[(0, "NINTY_PERCENT_SUCCEEDED"), (1, "ALL_RUNS_SUCCEEDED")], null=True),
                ),
                ("run_type", models.IntegerField(choices=[(0, "AGGREGATE"), (1, "INDIVIDUAL")])),
                (
                    "from_operator",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="from_triggers",
                        to="operator_manager.operator",
                    ),
                ),
                (
                    "to_operator",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="to_triggers",
                        to="operator_manager.operator",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
