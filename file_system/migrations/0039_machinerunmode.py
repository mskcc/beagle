# Generated by Django 2.2.28 on 2023-09-06 16:32

from django.db import migrations, models
import file_system.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0038_auto_20230424_0751"),
    ]

    operations = [
        migrations.CreateModel(
            name="MachineRunMode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_date", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("machine_name", file_system.models.LowercaseCharField(max_length=32, unique=True)),
                ("machine_class", file_system.models.LowercaseCharField(max_length=32)),
                ("machine_type", models.CharField(max_length=32)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]