# Generated by Django 2.2.28 on 2024-12-20 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0042_auto_20241220_0906"),
    ]

    operations = [
        migrations.AlterField(
            model_name="filemetadata",
            name="latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="filemetadata",
            name="version",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="patient",
            name="latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="patient",
            name="version",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="request",
            name="latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="request",
            name="request_id",
            field=models.CharField(default="REQUEST_ID", max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="request",
            name="version",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="sample",
            name="latest",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="sample",
            name="version",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name="filemetadata",
            unique_together={("file", "version")},
        ),
        migrations.AlterUniqueTogether(
            name="patient",
            unique_together={("patient_id", "version")},
        ),
        migrations.AlterUniqueTogether(
            name="request",
            unique_together={("request_id", "version")},
        ),
        migrations.AlterUniqueTogether(
            name="sample",
            unique_together={("sample_id", "version")},
        )
        # migrations.AddIndex(
        #     model_name="filemetadata",
        #     index=models.Index(fields=["latest"], name="latest_idx"),
        # ),
    ]
