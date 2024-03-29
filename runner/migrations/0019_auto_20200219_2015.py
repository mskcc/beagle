# Generated by Django 2.2.9 on 2020-02-19 20:15

from django.db import migrations, models
import django.db.models.deletion
import runner.models


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0013_auto_20200210_1902"),
        ("runner", "0018_auto_20200218_1921"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="operatorrun",
            name="app",
        ),
        migrations.RemoveField(
            model_name="operatorrun",
            name="name",
        ),
        migrations.RemoveField(
            model_name="operatortrigger",
            name="type",
        ),
        migrations.AddField(
            model_name="operatorrun",
            name="num_completed_runs",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="operatorrun",
            name="num_failed_runs",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="operatorrun",
            name="num_total_runs",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="operatorrun",
            name="operator",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="beagle_etl.Operator"),
        ),
        migrations.AlterField(
            model_name="operatorrun",
            name="status",
            field=models.IntegerField(
                choices=[(0, "CREATING"), (1, "READY"), (2, "RUNNING"), (3, "FAILED"), (4, "COMPLETED")],
                default=runner.models.RunStatus(0),
            ),
        ),
        migrations.AlterField(
            model_name="operatortrigger",
            name="condition",
            field=models.IntegerField(choices=[(0, "NINTY_PERCENT_COMPLETE"), (1, "ALL_RUNS_COMPLETE")]),
        ),
    ]
