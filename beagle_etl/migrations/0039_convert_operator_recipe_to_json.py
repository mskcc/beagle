from django.db import migrations
from django.contrib.postgres.fields import JSONField


METADATA_KEY = "genePanel"

def convert_recipes_to_json(apps, schema_editor):
    Operator = apps.get_model("beagle_etl", "Operator")
    for obj in Operator.objects.all():
        current_val = obj.recipes  # this was a string
        obj.recipes = {METADATA_KEY: [current_val] if current_val else []}
        obj.save(update_fields=["recipes"])


class Migration(migrations.Migration):

    dependencies = [
        ("beagle_etl", "0040_auto_20250603_1535"), 
    ]

    operations = [
        migrations.AlterField(
            model_name="operator",
            name="recipes",
            field=JSONField(default=dict),
        ),
        migrations.RunPython(convert_recipes_to_json, reverse_code=migrations.RunPython.noop),
    ]
