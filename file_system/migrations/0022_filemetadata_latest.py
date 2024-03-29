# Generated by Django 2.2.11 on 2020-10-07 03:26

from django.db import migrations, models


def set_latest(apps, schema_editor):
    File = apps.get_model("file_system", "File")

    files = File.objects.all()
    for f in files:
        metadata = f.filemetadata_set.order_by("-created_date").first()
        if metadata:
            metadata.latest = True
            metadata.save()
        else:
            print("File doesn't have metadata")
            print(f.id)


class Migration(migrations.Migration):

    dependencies = [
        ("file_system", "0021_add_samples"),
    ]

    operations = [
        migrations.AddField(
            model_name="filemetadata",
            name="latest",
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.RunPython(set_latest),
    ]
