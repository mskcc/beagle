# Generated by Django 2.2.28 on 2022-11-14 09:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("file_system", "0032_filegroup_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="filegroup",
            name="owner",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
