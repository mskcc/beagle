# Generated by Django 2.2.24 on 2021-08-31 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0027_auto_20210804_1508"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="delivery_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
