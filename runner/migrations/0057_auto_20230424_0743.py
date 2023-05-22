# Generated by Django 2.2.28 on 2023-04-24 11:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0037_auto_20230424_0743"),
        ("runner", "0056_auto_20230328_0948"),
    ]

    operations = [
        migrations.CreateModel(
            name="PipelineName",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name="run",
            name="requests",
            field=models.ManyToManyField(to="file_system.Request"),
        ),
        migrations.AddField(
            model_name="pipeline",
            name="pipeline_name",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="runner.PipelineName"
            ),
        ),
    ]