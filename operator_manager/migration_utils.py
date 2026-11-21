"""
Raw SQL copy of OperatorRun / OperatorTrigger rows between the runner and operator_manager tables.

Used by operator_manager 0004 (runner -> operator_manager) and by the reverse of runner 0069
(operator_manager -> runner). SQL instead of the ORM so that ids and created/modified dates are
preserved exactly (auto_now/auto_now_add would overwrite them) and large tables are copied in one statement.
"""

OPERATOR_RUN_COLUMNS = (
    "id",
    "created_date",
    "modified_date",
    "status",
    "operator_id",
    "num_total_runs",
    "num_manual_restarts",
    "triggered_alert",
    "num_completed_runs",
    "num_failed_runs",
    "job_group_id",
    "job_group_notifier_id",
    "finished_date",
    "parent_id",
)

OPERATOR_TRIGGER_COLUMNS = (
    "id",
    "created_date",
    "modified_date",
    "from_operator_id",
    "to_operator_id",
    "aggregate_condition",
    "run_type",
)


def copy_rows(schema_editor, src_table, dst_table, columns, operator_columns, operator_table):
    """
    INSERT INTO dst SELECT ... FROM src, skipping rows already present in dst.
    Operator ids that don't exist in operator_table are set to NULL (matches the FKs' on_delete=SET_NULL).
    """
    q = schema_editor.quote_name
    select = []
    for column in columns:
        if column in operator_columns:
            select.append(
                "CASE WHEN EXISTS (SELECT 1 FROM {op} o WHERE o.id = s.{col}) THEN s.{col} END".format(
                    op=q(operator_table), col=q(column)
                )
            )
        else:
            select.append("s.{}".format(q(column)))
    sql = (
        "INSERT INTO {dst} ({cols}) SELECT {select} FROM {src} s "
        "WHERE NOT EXISTS (SELECT 1 FROM {dst} d WHERE d.id = s.id)"
    ).format(
        dst=q(dst_table),
        src=q(src_table),
        cols=", ".join(q(c) for c in columns),
        select=", ".join(select),
    )
    schema_editor.execute(sql)


def copy_operator_runs_and_triggers(apps, schema_editor, src_app, dst_app, operator_model):
    operator_table = apps.get_model(*operator_model.split("."))._meta.db_table
    for model_name, columns, operator_columns in (
        ("OperatorTrigger", OPERATOR_TRIGGER_COLUMNS, ("from_operator_id", "to_operator_id")),
        ("OperatorRun", OPERATOR_RUN_COLUMNS, ("operator_id",)),
    ):
        copy_rows(
            schema_editor,
            apps.get_model(src_app, model_name)._meta.db_table,
            apps.get_model(dst_app, model_name)._meta.db_table,
            columns,
            operator_columns,
            operator_table,
        )
