# Generated by Django 2.2.10 on 2020-06-13 00:05

from django.db import migrations, models
import runner.models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0028_auto_20200608_1505"),
    ]

    operations = [
        migrations.AlterField(
            model_name="executionevents",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="operatorerrors",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="operatorrun",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="operatorrun",
            name="finished_date",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="operatorrun",
            name="status",
            field=models.IntegerField(
                choices=[(0, "CREATING"), (1, "READY"), (2, "RUNNING"), (3, "FAILED"), (4, "COMPLETED")],
                db_index=True,
                default=runner.models.RunStatus(0),
            ),
        ),
        migrations.AlterField(
            model_name="operatortrigger",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="pipeline",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="port",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="created_date",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="finished_date",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="status",
            field=models.IntegerField(
                choices=[(0, "CREATING"), (1, "READY"), (2, "RUNNING"), (3, "FAILED"), (4, "COMPLETED")], db_index=True
            ),
        ),
    ]
