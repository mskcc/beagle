# Generated by Django 2.2.9 on 2020-02-18 19:21

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0013_auto_20200210_1902"),
        ("runner", "0017_pipeline_operator"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperatorTrigger",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("type", models.IntegerField(choices=[(0, "ONE_TO_ONE"), (1, "MANY_TO_ONE")])),
                ("condition", models.IntegerField(choices=[(0, "ONE_RUN_COMPLETE"), (1, "ALL_RUNS_COMPLETE")])),
                (
                    "from_operator",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="from_triggers",
                        to="beagle_etl.Operator",
                    ),
                ),
                (
                    "to_operator",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="to_triggers",
                        to="beagle_etl.Operator",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="OperatorRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=400)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(0, "CREATING"), (1, "READY"), (2, "RUNNING"), (3, "FAILED"), (4, "COMPLETED")]
                    ),
                ),
                (
                    "app",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="runner.Pipeline"),
                ),
                (
                    "trigger",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to="runner.OperatorTrigger"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="run",
            name="operator_run",
            field=models.ForeignKey(
                default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to="runner.OperatorRun"
            ),
            preserve_default=False,
        ),
    ]
