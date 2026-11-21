from django.core.management.color import no_style
from django.db import migrations

V1 = 0  # OperatorVersion.V1
READY = 1  # OperatorStatus.READY


def migrate_operators(apps, schema_editor):
    EtlOperator = apps.get_model("beagle_etl", "Operator")
    Operator = apps.get_model("operator_manager", "Operator")
    db_alias = schema_editor.connection.alias

    Operator.objects.using(db_alias).bulk_create(
        [
            # Keep the same id so existing references to the legacy operators stay meaningful
            Operator(
                id=op.id,
                name=op.slug,
                type=V1,
                class_name=op.class_name,
                version=op.version,
                status=READY,
                trigger=list(op.recipes or []),
                notifier_id=op.notifier_id,
                active=op.active,
            )
            for op in EtlOperator.objects.using(db_alias).order_by("id")
            if not Operator.objects.using(db_alias).filter(id=op.id).exists()
        ]
    )

    # Explicit ids don't advance the sequence; reset it so new operators don't collide
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [Operator]):
            cursor.execute(sql)


def remove_operators(apps, schema_editor):
    Operator = apps.get_model("operator_manager", "Operator")
    Operator.objects.using(schema_editor.connection.alias).filter(type=V1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("operator_manager", "0001_initial"),
        ("beagle_etl", "0048_alter_etlconfiguration_id_alter_operator_id_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_operators, remove_operators),
    ]
