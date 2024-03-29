# Generated by Django 2.2.11 on 2020-08-27 13:56

from django.db import migrations

existing_operators = {
    "TempoOperator": {
        "version": "v1.0.0",
        "class_name": "runner.operator.tempo_operator.v1_0_0.tempo_operator.TempoOperator",
    },
    "ArgosOperator": {
        "version": "v1.0.0",
        "class_name": "runner.operator.argos_operator.v1_0_0.argos_operator.ArgosOperator",
    },
    "AccessOperator": {
        "version": "v1.0.0",
        "class_name": "runner.operator.access_operator.v1_0_0.access_operator.AccessOperator",
    },
    "ArgosQcOperator": {
        "version": "v1.0.0",
        "class_name": "runner.operator.argos_qc_operator.v1_0_0.argos_qc_operator.ArgosQcOperator",
    },
    "CopyOutputsOperator": {
        "version": "v1.0.0",
        "class_name": "runner.operator.copy_outputs_operator.v1_0_0.copy_outputs_operator.CopyOutputsOperator",
    },
    "HelixFiltersOperator": {
        "version": "v20.07.1",
        "class_name": "runner.operator.helix_filters.v20_07_1.helix_filters_operator.HelixFiltersOperator",
    },
}

new_operators = [
    {
        "slug": "ArgosOperator",
        "version": "v1.1.0",
        "class_name": "runner.operator.argos_operator.v1_1_0.argos_operator.ArgosOperator",
    },
    {
        "slug": "ArgosQcOperator",
        "version": "v1.1.0",
        "class_name": "runner.operator.argos_qc_operator.v1_1_0.argos_qc_operator.ArgosQcOperator",
    },
    {
        "slug": "CopyOutputsOperator",
        "version": "v1.1.0",
        "class_name": "runner.operator.copy_outputs_operator.v1_1_0.copy_outputs_operator.CopyOutputsOperator",
    },
    {
        "slug": "HelixFiltersOperator",
        "version": "v20.08.1",
        "class_name": "runner.operator.helix_filters.v20_08_1.helix_filters_operator.HelixFiltersOperator",
    },
    {
        "slug": "AionOperator",
        "version": "v1.0.0",
        "class_name": "runner.operator.aion.v1_0_0.aion_operator.AionOperator",
    },
    {
        "slug": "AccessFastqToBamOperator",
        "version": "v1.0.0",
        "class_name": "runner.operator.access.v1_0_0.fastq_to_bam.AccessFastqToBamOperator",
    },
]


def migrate_operator_values(apps, _):
    Operator = apps.get_model("beagle_etl", "Operator")
    for k, v in existing_operators.items():
        try:
            op = Operator.objects.get(class_name=k)
        except Operator.DoesNotExist:
            continue
        op.slug = k
        op.class_name = v["class_name"]
        op.version = v["version"]
        op.save()
    for o in new_operators:
        try:
            Operator.objects.create(slug=o["slug"], class_name=o["class_name"], version=o["version"], recipes=[])
        except Exception:
            print("Failed to create operator for class %s" % op["class_name"])


def revert_migration(apps, _):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0027_auto_20200827_0155"),
    ]

    operations = [
        migrations.RunPython(migrate_operator_values, reverse_code=revert_migration),
    ]
