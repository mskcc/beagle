# Generated by Django 2.2.24 on 2021-07-28 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0024_auto_20210722_1303"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sample",
            name="sample_id",
            field=models.CharField(max_length=32),
        ),
    ]
