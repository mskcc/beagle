# Generated by Django 2.2.11 on 2020-08-27 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("runner", "0033_add_lab_head_email_to_helix_filters_runs"),
    ]

    operations = [
        migrations.AddField(
            model_name="pipeline",
            name="default",
            field=models.BooleanField(default=False),
        ),
    ]
