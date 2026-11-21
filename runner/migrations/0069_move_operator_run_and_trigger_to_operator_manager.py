import django.db.models.deletion
from django.db import migrations, models
from operator_manager.migration_utils import copy_operator_runs_and_triggers


def copy_back(apps, schema_editor):
    # Reverse only: the old runner tables were just recreated empty, refill them before Run.operator_run points back
    copy_operator_runs_and_triggers(
        apps, schema_editor, src_app="operator_manager", dst_app="runner", operator_model="beagle_etl.Operator"
    )


class Migration(migrations.Migration):
    """
    OperatorRun and OperatorTrigger moved to operator_manager (rows copied by operator_manager 0004 with the same
    ids), and Pipeline.operator now points at operator_manager.Operator (ids preserved by operator_manager 0002).
    """

    dependencies = [
        ("operator_manager", "0004_copy_runner_operator_runs_and_triggers"),
        ("runner", "0068_alter_executionevents_outputs_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="run",
            name="operator_run",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runs",
                to="operator_manager.operatorrun",
            ),
        ),
        migrations.AlterField(
            model_name="pipeline",
            name="operator",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="operator_manager.operator"
            ),
        ),
        migrations.RunPython(migrations.RunPython.noop, copy_back),
        migrations.RemoveField(
            model_name="operatortrigger",
            name="from_operator",
        ),
        migrations.RemoveField(
            model_name="operatortrigger",
            name="to_operator",
        ),
        migrations.DeleteModel(
            name="OperatorRun",
        ),
        migrations.DeleteModel(
            name="OperatorTrigger",
        ),
    ]
