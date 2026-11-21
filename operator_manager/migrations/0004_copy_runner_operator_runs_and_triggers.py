from django.db import migrations
from operator_manager.migration_utils import copy_operator_runs_and_triggers


def forward(apps, schema_editor):
    copy_operator_runs_and_triggers(
        apps, schema_editor, src_app="runner", dst_app="operator_manager", operator_model="operator_manager.Operator"
    )


def backward(apps, schema_editor):
    # Rows are copied back to runner by the reverse of runner 0069, which runs before this
    for model_name in ("OperatorRun", "OperatorTrigger"):
        apps.get_model("operator_manager", model_name).objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operator_manager", "0003_operatorrun_operatortrigger"),
        ("runner", "0068_alter_executionevents_outputs_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
