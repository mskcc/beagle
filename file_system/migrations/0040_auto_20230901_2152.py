# Generated by Django 2.2.28 on 2023-09-02 01:52

from django.db import migrations


data = [
    ["DIANA", "NovaSeq", "NovaSeq 6000"],
    ["JAX", "HiSeq", "HiSeq 4000"],
    ["KIM", "HiSeq", "HiSeq 2500"],
    ["LIZ", "HiSeq", "HiSeq 2500"],
    ["MICHELLE", "NovaSeq", "NovaSeq 6000"],
    ["MOMO", "HiSeq", "HiSeq 2500"],
    ["PITT", "HiSeq", "HiSeq 4000"],
    ["RUTH", "NovaSeq", "NovaSeq 6000"],
]


def load_machine_names(apps, schema_editor):
    MachineRunMode = apps.get_model("file_system", "MachineRunMode")
    for row in data:
        try:
            MachineRunMode.objects.create(machine_name=row[0], machine_class=row[1], machine_type=row[2])
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0039_machinerunmode"),
    ]

    operations = [migrations.RunPython(load_machine_names, migrations.RunPython.noop)]
